pipeline {
    agent any

    environment {
        DEPLOY_PATH = "${params.DEPLOY_PATH}"
    }

    stages {
        stage('Deploy') {
            steps {
                sh '''
                    git config --global --add safe.directory "${DEPLOY_PATH}"
                    cd $DEPLOY_PATH
                    git pull origin prod
                    docker-compose down
                    docker-compose up -d --build
                '''
            }
        }
    }
}