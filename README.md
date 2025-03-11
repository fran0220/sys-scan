# 股票分析系统 (Stock Analysis System)

## 简介

基于 https://github.com/DR-lin-eng/stock-scanner 二次修改，感谢原作者  

## 功能变更

1. 增加html页面，支持浏览器在线使用  
2. 增加港股、美股支持  
3. 完善Dockerfile、GitHub Actions 支持docker一键部署使用  
4. 支持x86_64 和 ARM64架构镜像  
5. 支持流式输出，支持前端传入Key(仅作为本地用户使用，日志等内容不会输出) 感谢@Cassianvale  
6. 重构为Vue3+Vite+TS+Naive UI，支持响应式布局  
7. 支持GitHub Actions 一键部署  
8. 支持Nginx反向代理，可通过80/443端口访问
9. 新增期货分析功能，支持国内主要期货品种的技术分析和行情查询

## 期货分析功能

最新版本增加了期货分析功能，可以对国内主要期货品种进行技术分析和行情查询。

### 主要特性

- 支持国内主要期货交易所（上期所、大商所、郑商所、中金所）的期货品种
- 提供期货品种的K线图、成交量、持仓量等技术指标分析
- 支持期货品种的搜索和快速查询
- 提供期货合约的基本信息和最新行情数据
- 支持期货分析结果的导出和分享

### 技术实现

- 前端使用Vue3+TypeScript实现，确保类型安全和代码质量
- 使用Axios进行API请求，并添加了完善的类型定义
- 实现了请求和响应拦截器，支持JWT认证和错误处理
- 使用自定义Logger工具进行日志记录，便于调试和问题排查
- 后端使用Python FastAPI实现，支持异步处理和流式响应

### 在Ubuntu服务器上部署

对于Ubuntu x64服务器，推荐以下部署步骤：

```bash
# 克隆仓库
git clone https://github.com/cassianvale/stock-scanner.git
cd stock-scanner

# 创建并配置.env文件
cp .env.example .env
# 编辑.env文件，配置必要的API密钥和其他参数

# 安装系统依赖
sudo apt-get update
sudo apt-get install -y python3-dev python3-venv libxml2-dev libxslt1-dev nodejs npm

# 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
cd ..

# 启动后端服务
python web_server.py &

# 启动前端开发服务器
cd frontend
npm run dev
```

### 注意事项

- 期货分析功能需要配置正确的API密钥才能使用
- 在Ubuntu环境下测试和部署可以避免Mac环境下可能遇到的依赖问题
- 确保服务器有足够的内存和CPU资源，特别是在处理大量期货数据时
- 建议使用Python 3.10或更高版本，但避免使用3.13版本，以确保最佳兼容性

## Docker镜像一键部署

```
# 拉取最新版本
docker pull cassianvale/stock-scanner:latest

# 启动主应用容器
docker run -d \
  --name stock-scanner-app \
  --network stock-scanner-network \
  -p 8888:8888 \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/data:/app/data" \
  -e API_KEY="你的API密钥" \
  -e API_URL="你的API地址" \
  -e API_MODEL="你的API模型" \
  -e API_TIMEOUT="60" \
  -e LOGIN_PASSWORD="你的登录密码" \
  -e ANNOUNCEMENT_TEXT="你的公告内容" \
  --restart unless-stopped \
  cassianvale/stock-scanner:latest
  
# 运行Nginx容器
docker run -d \
  --name stock-scanner-nginx \
  --network stock-scanner-network \
  -p 80:80 \
  -p 443:443 \
  -v "$(pwd)/nginx/nginx.conf:/etc/nginx/conf.d/default.conf" \
  -v "$(pwd)/nginx/logs:/var/log/nginx" \
  -v "$(pwd)/nginx/ssl:/etc/nginx/ssl" \
  --restart unless-stopped \
  nginx:stable-alpine

针对API_URL处理兼容更多的api地址，规则与Cherry Studio一致， /结尾忽略v1版本，#结尾强制使用输入地址。
API_URL 处理逻辑说明：
1. 当 API_URL 以 / 结尾时直接追加 chat/completions，保留原有版本号：
  示例：
   输入: https://ark.cn-beijing.volces.com/api/v3/
   输出: https://ark.cn-beijing.volces.com/api/v3/chat/completions
2. 当 API_URL 以 # 结尾时强制使用当前链接：
  示例：
   输入: https://ark.cn-beijing.volces.com/api/v3/chat/completions#
   输出: https://ark.cn-beijing.volces.com/api/v3/chat/completions
3. 当 API_URL 不以 / 结尾时使用默认版本号 v1：
  示例：
   输入: https://ark.cn-beijing.volces.com/api
   输出: https://ark.cn-beijing.volces.com/api/v1/chat/completions


```

默认8888端口，部署完成后访问  http://你的域名或ip:8888 即可使用  

## 使用Nginx反向代理

项目已集成Nginx服务，可以通过80端口(HTTP)和443端口(HTTPS)访问应用  
使用docker-compose启动：  

```shell
# 克隆仓库
git clone https://github.com/cassianvale/stock-scanner.git
cd stock-scanner

# 创建.env文件并填写必要的环境变量
cat > .env << EOL
API_KEY=你的API密钥
API_URL=你的API地址
API_MODEL=你的API模型
API_TIMEOUT=超时时间(默认60秒)
LOGIN_PASSWORD=登录密码(可选)
ANNOUNCEMENT_TEXT=公告文本
EOL

# 创建SSL证书目录
mkdir -p nginx/ssl

# 生成自签名SSL证书（仅用于测试环境）
openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

# 启动服务
docker-compose up -d
```

### 使用自己的SSL证书

如果您有自己的SSL证书，可以替换自签名证书：

1. 将您的证书文件放在 `nginx/ssl/` 目录下
2. 确保证书文件命名为 `fullchain.pem`，私钥文件命名为 `privkey.pem`
3. 重启服务: `docker-compose restart nginx`

相关参考：[免费泛域名 SSL 证书申请及自动续期（使用 1Panel 面板）](https://bronya-zaychik.cn/archives/GenSSL.html)

## Github Actions 部署

| 环境变量 | 说明 |
| --- | --- |
| DOCKERHUB_USERNAME | Docker Hub用户名 |
| DOCKERHUB_TOKEN | Docker Hub访问令牌 |
| SERVER_HOST | 部署服务器地址 |
| SERVER_USERNAME | 服务器用户名 |
| SSH_PRIVATE_KEY | SSH私钥 |
| DEPLOY_PATH | 部署路径 |
| SLACK_WEBHOOK | Slack通知Webhook（可选） |


## 注意事项 (Notes)
- 股票分析仅供参考，不构成投资建议
- 使用前请确保网络连接正常
- 建议在实盘前充分测试

## 贡献 (Contributing)
欢迎提交 issues 和 pull requests！

## 许可证 (License)
[待添加具体许可证信息]

## 免责声明 (Disclaimer)
本系统仅用于学习和研究目的，投资有风险，入市需谨慎。
