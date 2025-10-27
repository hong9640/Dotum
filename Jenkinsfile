pipeline {
    agent any
    
    environment {
        DOCKER_COMPOSE = 'docker-compose'
        PROJECT_NAME = 'dotum'
        // Mattermost Webhook URL (Optional)
        MATTERMOST_WEBHOOK_URL = "${env.MATTERMOST_WEBHOOK_URL ?: ''}"
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
                    
                    // 호스트의 .env 파일을 workspace로 복사
                    sh '''
                        if [ -f /home/ubuntu/.env ]; then
                            cp /home/ubuntu/.env .env
                            echo "✅ .env 파일 복사 완료"
                        else
                            echo "⚠️ /home/ubuntu/.env 파일이 없습니다"
                        fi
                    '''
                    
                    // .env 파일에서 MATTERMOST_WEBHOOK_URL 읽기
                    if (fileExists('.env')) {
                        def envFile = readFile('.env')
                        def lines = envFile.split('\n')
                        for (String line : lines) {
                            if (line.startsWith('MATTERMOST_WEBHOOK_URL=')) {
                                env.MATTERMOST_WEBHOOK_URL = line.split('=', 2)[1].trim()
                                echo "📢 Mattermost Webhook URL 설정됨"
                                break
                            }
                        }
                    }
                    
                    // 변경된 파일 확인
                    def changedFiles = sh(
                        script: 'git diff --name-only HEAD~1 HEAD',
                        returnStdout: true
                    ).trim()
                    
                    echo "📝 변경된 파일:"
                    echo changedFiles
                    
                    // 변경 감지
                    env.BACKEND_CHANGED = 'false'
                    env.FRONTEND_CHANGED = 'false'
                    env.FULL_DEPLOY = 'false'
                    
                    if (changedFiles.contains('backend/')) {
                        env.BACKEND_CHANGED = 'true'
                    }
                    
                    if (changedFiles.contains('FE/')) {
                        env.FRONTEND_CHANGED = 'true'
                    }
                    
                    if (changedFiles.contains('docker-compose.yml') || changedFiles.contains('Jenkinsfile')) {
                        env.FULL_DEPLOY = 'true'
                    }
                    
                    echo "변경 상태: BACKEND=${env.BACKEND_CHANGED}, FRONTEND=${env.FRONTEND_CHANGED}, FULL=${env.FULL_DEPLOY}"
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
                        # 기존 backend, frontend 컨테이너 강제 재생성
                        ${DOCKER_COMPOSE} up -d --force-recreate --no-deps backend frontend || true
                        # 실패 시 기존 컨테이너 제거 후 재시작
                        docker rm -f backend frontend 2>/dev/null || true
                        ${DOCKER_COMPOSE} up -d backend frontend
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo '✅ 배포 성공!'
            script {
                // Mattermost 알림 (Webhook URL이 설정된 경우)
                if (env.MATTERMOST_WEBHOOK_URL) {
                    def payload = """
                    {
                        "username": "Jenkins",
                        "icon_url": "https://jenkins.io/images/logos/jenkins/jenkins.png",
                        "text": "✅ **배포 성공**",
                        "attachments": [{
                            "color": "good",
                            "title": "${env.PROJECT_NAME} - 빌드 #${env.BUILD_NUMBER}",
                            "text": "✅ 배포가 성공적으로 완료되었습니다.\\n\\n🔗 [Jenkins Build](${env.BUILD_URL})",
                            "fields": [{
                                "short": true,
                                "title": "브랜치",
                                "value": "${env.GIT_BRANCH ?: 'unknown'}"
                            }, {
                                "short": true,
                                "title": "빌드 번호",
                                "value": "#${env.BUILD_NUMBER}"
                            }]
                        }]
                    }
                    """
                    sh """
                        curl -X POST '${env.MATTERMOST_WEBHOOK_URL}' \\
                            -H 'Content-Type: application/json' \\
                            -d '${payload}' || true
                    """
                }
            }
        }
        failure {
            echo '❌ 배포 실패!'
            script {
                // Mattermost 알림 (Webhook URL이 설정된 경우)
                if (env.MATTERMOST_WEBHOOK_URL) {
                    def payload = """
                    {
                        "username": "Jenkins",
                        "icon_url": "https://jenkins.io/images/logos/jenkins/jenkins.png",
                        "text": "❌ **배포 실패**",
                        "attachments": [{
                            "color": "danger",
                            "title": "${env.PROJECT_NAME} - 빌드 #${env.BUILD_NUMBER}",
                            "text": "❌ 배포 중 오류가 발생했습니다.\\n\\n🔗 [Jenkins Build](${env.BUILD_URL})",
                            "fields": [{
                                "short": true,
                                "title": "브랜치",
                                "value": "${env.GIT_BRANCH ?: 'unknown'}"
                            }, {
                                "short": true,
                                "title": "빌드 번호",
                                "value": "#${env.BUILD_NUMBER}"
                            }]
                        }]
                    }
                    """
                    sh """
                        curl -X POST '${env.MATTERMOST_WEBHOOK_URL}' \\
                            -H 'Content-Type: application/json' \\
                            -d '${payload}' || true
                    """
                }
            }
        }
        always {
            echo '🧹 정리 중...'
            cleanWs()
        }
    }
}

