pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    triggers {
        // Local Docker lab: Jenkins checks GitHub without a public endpoint.
        pollSCM('H/5 * * * *')
    }

    environment {
        PYTHONUTF8 = '1'
        PIP_DISABLE_PIP_VERSION_CHECK = '1'
        APP_ENV = 'testing'
    }

    stages {
        stage('Checkout') {
            steps {
                // Clear previous evidence even if checkout fails before tests can run.
                dir('reports') { deleteDir() }
                dir('.scannerwork') { deleteDir() }
                script {
                    def revision = checkout scm
                    env.CI_BRANCH = (revision.GIT_BRANCH ?: '').replaceFirst('^origin/', '')
                    if (!env.CI_BRANCH) {
                        error('Cannot determine checked-out branch; refuse ambiguous Sonar analysis')
                    }
                }
                sh 'mkdir -p reports'
            }
        }

        stage('Python 3.12 & Dependencies') {
            options { timeout(time: 10, unit: 'MINUTES') }
            steps {
                sh '''#!/usr/bin/env bash
set -euo pipefail
python3.12 -c 'import sys; assert sys.version_info[:2] == (3, 12), sys.version'
python3.12 -m venv --clear .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python tools/ci_checks.py metadata --reports reports
'''
            }
        }

        stage('Code Quality & AI Kit Validation') {
            steps {
                sh '''#!/usr/bin/env bash
set -euo pipefail
.venv/bin/python -m flake8 app tests tools --count --max-line-length=120 --statistics 2>&1 | tee reports/flake8.txt
.venv/bin/python -m black --check --line-length 120 app tests tools 2>&1 | tee reports/black.txt
.venv/bin/python n42-ai-kit/scripts/validate.py 2>&1 | tee reports/ai-kit.txt
'''
            }
        }

        stage('Security Scan') {
            steps {
                sh '''#!/usr/bin/env bash
set -euo pipefail
.venv/bin/python tools/check_sensitive.py . 2>&1 | tee reports/security-scan.txt
'''
            }
        }

        stage('Unit Tests & Coverage') {
            steps {
                sh '''#!/usr/bin/env bash
set -euo pipefail
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v 2>&1 | tee reports/unittest.txt
.venv/bin/python -m pytest tests/ -v --junitxml=reports/junit-report.xml --cov=app --cov-report=xml:reports/coverage.xml --cov-report=html:reports/coverage-html 2>&1 | tee reports/pytest.txt
'''
            }
        }

        stage('API Health Smoke') {
            options { timeout(time: 2, unit: 'MINUTES') }
            steps {
                sh '.venv/bin/python tools/ci_checks.py health --reports reports'
            }
        }

        stage('SonarQube Analysis (main)') {
            when { expression { env.CI_BRANCH == 'main' } }
            options { timeout(time: 10, unit: 'MINUTES') }
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'
                    withEnv(["SCANNER_HOME=${scannerHome}"]) {
                        withSonarQubeEnv('SonarQube-N42') {
                            sh '''#!/usr/bin/env bash
set -euo pipefail
test -s reports/coverage.xml
"$SCANNER_HOME/bin/sonar-scanner"
'''
                        }
                    }
                }
            }
        }

        stage('Quality Gate (main)') {
            when { expression { env.CI_BRANCH == 'main' } }
            options { timeout(time: 10, unit: 'MINUTES') }
            steps {
                script {
                    // Explicit error makes a non-OK gate FAILURE, rather than only UNSTABLE.
                    def gate = waitForQualityGate()
                    writeFile file: 'reports/quality-gate.txt', text: "status=${gate.status}\n"
                    if (gate.status != 'OK') {
                        error("SonarQube Quality Gate failed: ${gate.status}")
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                try {
                    if (fileExists('reports/junit-report.xml')) {
                        junit testResults: 'reports/junit-report.xml', allowEmptyResults: false
                    }
                } finally {
                    archiveArtifacts artifacts: 'reports/**, .scannerwork/report-task.txt', allowEmptyArchive: true
                }
            }
        }
        success {
            echo 'Jenkins checks passed. SonarQube gate applies only to the main job.'
        }
        failure {
            echo 'Jenkins checks or SonarQube Quality Gate failed; inspect archived reports.'
        }
    }
}
