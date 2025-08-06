pipeline {
    agent any

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