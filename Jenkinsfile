pipeline {
    agent any
    
    environment {
        DOCKER_COMPOSE = 'docker-compose'
        PROJECT_NAME = 'dotum'
        // Mattermost Webhook URL은 .env 파일에서 로드됨
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
            
            // 변경된 서비스 확인
            def backendChanged = env.BACKEND_CHANGED == 'true'
            def frontendChanged = env.FRONTEND_CHANGED == 'true'
            def fullDeploy = env.FULL_DEPLOY == 'true'
            
            def deployBackend = backendChanged || fullDeploy
            def deployFrontend = frontendChanged || fullDeploy
            
            echo "📦 배포 대상 - Backend: ${deployBackend}, Frontend: ${deployFrontend}"
            
            sh """
                cd ${WORKSPACE}
                
                # 배포 대상 컨테이너만 선택적으로 처리
                DEPLOY_SERVICES=""
                
                if [ "${deployBackend}" = "true" ]; then
                    DEPLOY_SERVICES="\${DEPLOY_SERVICES} backend"
                fi
                
                if [ "${deployFrontend}" = "true" ]; then
                    DEPLOY_SERVICES="\${DEPLOY_SERVICES} frontend"
                fi
                
                echo "📦 배포 대상: \${DEPLOY_SERVICES}"
                
                # 1단계: 기존 컨테이너 확실히 제거
                echo "🗑️ 기존 컨테이너 제거 중..."
                for service in \${DEPLOY_SERVICES}; do
                    echo "  - dotum-\${service} 제거"
                    # 이름으로 제거 시도
                    docker stop dotum-\${service} 2>/dev/null || true
                    docker rm -f dotum-\${service} 2>/dev/null || true
                    # 혹시 모를 경우를 위해 컨테이너 ID로도 제거
                    CONTAINER_ID=\$(docker ps -a --filter "name=dotum-\${service}" --format "{{.ID}}" | head -1)
                    if [ ! -z "\${CONTAINER_ID}" ]; then
                        echo "    컨테이너 ID \${CONTAINER_ID} 제거"
                        docker rm -f \${CONTAINER_ID} 2>/dev/null || true
                    fi
                done
                
                # 제거 후 확인
                echo "🔍 제거 후 남은 컨테이너 확인:"
                docker ps -a --filter "name=dotum-" --format "{{.Names}} ({{.ID}})" || echo "없음"
                
                # 대기 시간 추가
                sleep 2
                
                # 2단계: 컨테이너 재생성 (새 이미지 적용)
                echo "🚀 새 컨테이너 생성 중..."
                ${DOCKER_COMPOSE} up -d --no-deps \${DEPLOY_SERVICES}
                
                # 3단계: 상태 확인
                echo "✅ 배포된 컨테이너 상태:"
                docker ps --filter "name=dotum-" --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"
            """
        }
    }
}

    }
    
    post {
        success {
            echo '✅ 배포 성공!'
            script {
                echo "🔍 Webhook URL 확인: ${env.MATTERMOST_WEBHOOK_URL ?: '설정되지 않음'}"
                // Mattermost 알림 (Webhook URL이 설정된 경우)
                if (env.MATTERMOST_WEBHOOK_URL) {
                    echo "📤 Mattermost 알림 발송 중..."
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
                    echo "✅ 알림 발송 완료"
                } else {
                    echo "⚠️ Webhook URL이 설정되지 않아 알림을 발송하지 않습니다"
                }
            }
        }
        failure {
            echo '❌ 배포 실패!'
            script {
                echo "🔍 Webhook URL 확인: ${env.MATTERMOST_WEBHOOK_URL ?: '설정되지 않음'}"
                // Mattermost 알림 (Webhook URL이 설정된 경우)
                if (env.MATTERMOST_WEBHOOK_URL) {
                    echo "📤 Mattermost 알림 발송 중..."
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
                    echo "✅ 알림 발송 완료"
                } else {
                    echo "⚠️ Webhook URL이 설정되지 않아 알림을 발송하지 않습니다"
                }
            }
        }
        always {
            echo '🧹 정리 중...'
            cleanWs()
        }
    }
}

