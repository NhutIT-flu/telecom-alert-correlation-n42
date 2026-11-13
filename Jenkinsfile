pipeline {
    agent any

    options {
        timestamps()
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    parameters {
        booleanParam(name: 'SONAR_REVIEW', defaultValue: false,
            description: 'Run Sonar on the isolated N42-10 validation project (feature only).')
        string(name: 'SONAR_REVIEW_TIMEOUT_SECONDS', defaultValue: '600',
            description: 'Review only: wait deadline 10..600 seconds. Main always uses 600 seconds.')
    }

    triggers {
        // Local Docker lab: Jenkins checks GitHub without a public endpoint.
        pollSCM('H/5 * * * *')
    }

    environment {
        PYTHONUTF8 = '1'
        PIP_DISABLE_PIP_VERSION_CHECK = '1'
        APP_ENV = 'testing'
        N42_UDP_HOST = '127.0.0.1'
        N42_UDP_PORT = '0'
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
                    env.CI_COMMIT = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                    env.CI_SONAR_PROJECT = env.CI_BRANCH == 'main' ? 'n42-telecom-alert' :
                        (params.SONAR_REVIEW ? 'n42-telecom-alert-ci-validation' : '')
                    currentBuild.displayName = "#${env.BUILD_NUMBER} ${env.CI_BRANCH} ${env.CI_COMMIT.take(8)}"
                    currentBuild.description = "Revision ${env.CI_COMMIT}"
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

        stage('UDP Buffer Preflight') {
            options { timeout(time: 1, unit: 'MINUTES') }
            steps {
                sh '''#!/usr/bin/env bash
set -euo pipefail
.venv/bin/python tools/udp_buffer_preflight.py --prepare 2>&1 | tee reports/udp-buffer.txt
'''
            }
        }

        stage('Code Quality & AI Kit Validation') {
            steps {
                sh '''#!/usr/bin/env bash
set -euo pipefail
.venv/bin/python -m flake8 app tests tools --count --statistics 2>&1 | tee reports/flake8.txt
.venv/bin/python -m black --check --diff app tests tools 2>&1 | tee reports/black.txt
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

        stage('SonarQube Analysis') {
            when { expression { env.CI_SONAR_PROJECT } }
            options { timeout(time: 10, unit: 'MINUTES') }
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'
                    withEnv(["SCANNER_HOME=${scannerHome}"]) {
                        withSonarQubeEnv('SonarQube-N42') {
                            sh '''#!/usr/bin/env bash
set -euo pipefail
test -s reports/coverage.xml
"$SCANNER_HOME/bin/sonar-scanner" \
    "-Dsonar.projectKey=$CI_SONAR_PROJECT" \
    "-Dsonar.scm.revision=$CI_COMMIT" \
    "-Dsonar.projectVersion=build-$BUILD_NUMBER" \
    "-Dsonar.buildString=$BUILD_URL"
'''
                        }
                    }
                }
            }
        }

        stage('Quality Gate') {
            when { expression { env.CI_SONAR_PROJECT } }
            steps {
                script {
                    def status = 'WAITING'
                    def waitSeconds = 600
                    if (env.CI_BRANCH != 'main') {
                        def requested = params.SONAR_REVIEW_TIMEOUT_SECONDS ?: '600'
                        if (!(requested ==~ /\d{1,3}/) || requested.toInteger() < 10 || requested.toInteger() > 600) {
                            error('SONAR_REVIEW_TIMEOUT_SECONDS must be 10..600')
                        }
                        waitSeconds = requested.toInteger()
                    }
                    try {
                        timeout(time: waitSeconds, unit: 'SECONDS') {
                            def gate = waitForQualityGate()
                            status = gate.status ?: 'UNKNOWN'
                        }
                        if (status != 'OK') {
                            error("SonarQube Quality Gate failed: ${status}")
                        }
                    } catch (org.jenkinsci.plugins.workflow.steps.FlowInterruptedException interrupted) {
                        if (interrupted.isActualInterruption()) {
                            status = 'ABORTED'
                            throw interrupted
                        }
                        status = 'TIMEOUT'
                        error('SonarQube Quality Gate wait timed out')
                    } finally {
                        writeFile file: 'reports/quality-gate.txt', text:
                            "status=${status}\nrevision=${env.CI_COMMIT}\nproject=${env.CI_SONAR_PROJECT}\nbuild=${env.BUILD_URL}\n"
                        currentBuild.description += " | Gate ${status}"
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
                    writeFile file: 'reports/build-result.txt', text:
                        "result=${currentBuild.currentResult}\nrevision=${env.CI_COMMIT ?: 'unknown'}\nbuild=${env.BUILD_URL}\n"
                    archiveArtifacts artifacts: 'reports/**, .scannerwork/report-task.txt', allowEmptyArchive: true
                }
            }
        }
        success {
            echo 'Jenkins checks passed. Sonar runs on main or the isolated review project.'
        }
        failure {
            echo 'Jenkins checks or SonarQube Quality Gate failed; inspect archived reports.'
        }
    }
}
