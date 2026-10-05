// Pipeline declarativo (legado de Jenkins): build, pruebas, SonarQube, Selenium y despliegue.
pipeline {
  agent { label 'docker' }
  options {
    timestamps()
    timeout(time: 45, unit: 'MINUTES')
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
  }
  environment {
    SONAR_HOST = credentials('sonar-host-url')   // credenciales siempre desde el vault de Jenkins
  }
  stages {
    stage('Checkout') { steps { checkout scm } }

    stage('Build & Unit tests') {
      parallel {
        stage('Java') {
          steps { dir('services/bucket-provisioner-java') { sh 'mvn -B -ntp verify' } }
          post { always { junit 'services/bucket-provisioner-java/target/surefire-reports/*.xml' } }
        }
        stage('Python') {
          steps {
            dir('services/bucket-auditor-python') {
              sh 'python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]" && pytest --junitxml=report.xml'
            }
          }
          post { always { junit 'services/bucket-auditor-python/report.xml' } }
        }
      }
    }

    stage('SonarQube') {
      steps {
        withSonarQubeEnv('sonarqube') {
          sh 'mvn -B -ntp -f services/bucket-provisioner-java/pom.xml sonar:sonar'
        }
        timeout(time: 10, unit: 'MINUTES') { waitForQualityGate abortPipeline: true }
      }
    }

    stage('IaC security scan') {
      steps { sh 'checkov -d iac --config-file security/checkov.yaml' }
    }

    stage('Deploy dev') {
      when { branch 'main' }
      steps {
        withAWS(role: 'portafolio-deploy-dev', roleAccount: '111122223333', region: 'us-east-1') {
          sh './scripts/deploy-cfn.sh dev'
        }
      }
    }

    stage('Selenium smoke tests') {
      when { branch 'main' }
      steps { sh 'echo "mvn -f e2e/pom.xml test -Denv=dev   # pruebas E2E de ejemplo"' }
    }

    stage('Approve prod') {
      when { branch 'main' }
      steps { input message: 'Desplegar a produccion?', submitter: 'release-managers' }
    }
  }
  post {
    failure { echo 'Pipeline fallido: notificar al canal de operaciones' }
    cleanup { cleanWs() }
  }
}
