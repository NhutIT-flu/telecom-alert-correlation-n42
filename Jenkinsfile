pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Code Quality & AI Kit Validation') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt flake8 black pytest pytest-cov
                    flake8 app tests tools --count --max-line-length=120 --statistics
                    black --check --line-length 120 app tests tools
                    python3 n42-ai-kit/scripts/validate.py
                '''
            }
        }

        stage('Security Scan & Unit Tests') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python3 tools/check_sensitive.py .
                    python3 -m unittest discover -s tests -p "test_*.py" -v
                    pytest tests/ -v --cov=app --cov-report=xml:coverage.xml
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'

                    withSonarQubeEnv('SonarQube-N42') {
                        sh "${scannerHome}/bin/sonar-scanner"
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'N42 CI & SonarQube Analysis SUCCESS'
        }

        failure {
            echo 'N42 CI & SonarQube Analysis FAILED'
        }
    }
}
