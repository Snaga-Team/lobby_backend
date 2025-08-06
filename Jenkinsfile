pipeline {
    agent any

    environment {
        DEPLOY_PATH = "/home/john/lobby_backend"
    }

    stages {
        stage('Deploy') {
            steps {
                sh '''
                    cd $DEPLOY_PATH
                    git pull origin prod
                    docker-compose down
                    docker-compose up -d --build
                '''
            }
        }
    }
}