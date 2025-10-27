pipeline {
    agent any
    
    environment {
        DOCKER_COMPOSE = 'docker-compose'
        PROJECT_NAME = 's13p31s201'
        // GitLab webhook을 위한 credentials ID
        GITLAB_CREDENTIALS_ID = 'gitlab-token'
    }
    
    triggers {
        // GitLab webhook trigger - master와 develop 브랜치에서만 실행
        // GitLab Settings → Webhooks에서 Secret Token 설정 필요
        gitlab(
            triggerOnPush: true, 
            triggerOnMergeRequest: true, 
            branchFilterType: 'NameBasedFilter',
            includeBranchesSpec: 'master,develop'
        )
    }
    
    stages {
        stage('Checkout') {
            steps {
                script {
                    echo '🔄 Git에서 코드 체크아웃 중...'
                    checkout scm
                    
                    // 변경된 파일 확인
                    sh '''
                        echo "📝 변경된 파일 확인 중..."
                        # 현재 브랜치의 최근 커밋과 그 이전 커밋 비교
                        git diff --name-only HEAD~1 HEAD > changes.txt || true
                        cat changes.txt
                        
                        if grep -q "^backend/" changes.txt; then
                            echo "BACKEND_CHANGED=true" > changed_files.env
                        fi
                        
                        if grep -q "^FE/" changes.txt; then
                            echo "FRONTEND_CHANGED=true" >> changed_files.env
                        fi
                        
                        # docker-compose.yml이나 Jenkinsfile 변경 시 전체 재배포
                        if grep -q "docker-compose.yml" changes.txt || grep -q "Jenkinsfile" changes.txt; then
                            echo "FULL_DEPLOY=true" >> changed_files.env
                        fi
                    '''
                    
                    load 'changed_files.env'
                }
            }
        }
        
        stage('Backend Build') {
            when {
                anyOf {
                    expression { return env.BACKEND_CHANGED == 'true' }
                    expression { return env.FULL_DEPLOY == 'true' }
                }
            }
            steps {
                script {
                    echo '🔨 Backend 빌드 중...'
                    sh """
                        cd ${WORKSPACE}
                        ${DOCKER_COMPOSE} build backend
                    """
                }
            }
        }
        
        stage('Frontend Build') {
            when {
                anyOf {
                    expression { return env.FRONTEND_CHANGED == 'true' }
                    expression { return env.FULL_DEPLOY == 'true' }
                }
            }
            steps {
                script {
                    echo '🔨 Frontend 빌드 중...'
                    sh """
                        cd ${WORKSPACE}
                        ${DOCKER_COMPOSE} build frontend
                    """
                }
            }
        }
        
        stage('Deploy') {
            when {
                anyOf {
                    expression { return env.BACKEND_CHANGED == 'true' }
                    expression { return env.FRONTEND_CHANGED == 'true' }
                    expression { return env.FULL_DEPLOY == 'true' }
                }
            }
            steps {
                script {
                    echo '🚀 배포 중...'
                    sh """
                        cd ${WORKSPACE}
                        ${DOCKER_COMPOSE} down
                        ${DOCKER_COMPOSE} up -d
                    """
                }
            }
        }
        
        stage('Health Check') {
            when {
                anyOf {
                    expression { return env.BACKEND_CHANGED == 'true' }
                    expression { return env.FRONTEND_CHANGED == 'true' }
                    expression { return env.FULL_DEPLOY == 'true' }
                }
            }
            steps {
                script {
                    echo '🏥 Health Check 중...'
                    sleep(time: 10, unit: 'SECONDS')
                    sh """
                        curl -f https://k13s201.p.ssafy.io/health || exit 1
                        curl -f https://k13s201.p.ssafy.io || exit 1
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo '✅ 배포 성공!'
        }
        failure {
            echo '❌ 배포 실패!'
        }
        always {
            echo '🧹 정리 중...'
            cleanWs()
        }
    }
}

