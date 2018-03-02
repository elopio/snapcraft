pipeline {
    agent any
    stages {
        stage('static') {
            steps {
                sh './tools/jenkins/run_tests.sh static 2>&1'
            }
        }
    }
}
