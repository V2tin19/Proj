"""后端 API 测试脚本"""

import json
import sys

import httpx

import os

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:3001")
client = httpx.Client(base_url=BASE_URL, timeout=30)

passed = 0
failed = 0


def test(name, method, path, expected_status=200, json_data=None):
    global passed, failed
    try:
        if method == "GET":
            r = client.get(path)
        elif method == "POST":
            r = client.post(path, json=json_data)
        elif method == "DELETE":
            r = client.delete(path)
        else:
            r = client.request(method, path, json=json_data)

        ok = r.status_code == expected_status
        if ok:
            print(f"  [OK] {name}")
            passed += 1
        else:
            print(f"  [FAIL] {name} -- status {r.status_code}, expected {expected_status}")
            print(f"    response: {r.text[:200]}")
            failed += 1
        return r
    except Exception as e:
        print(f"  [FAIL] {name} -- exception: {e}")
        failed += 1
        return None


def main():
    print("=" * 50)
    print("Backend API Test")
    print("=" * 50)

    # 1. 健康检查
    print("\n[1/8] 健康检查")
    r = test("GET /api/health", "GET", "/api/health")
    if r:
        data = r.json()
        assert data.get("ok") is True, "health.ok 应为 True"
        print(f"  → provider: {data.get('provider')}")

    # 2. 模板列表
    print("\n[2/8] 模板列表")
    r = test("GET /api/prompt-templates", "GET", "/api/prompt-templates")
    if r:
        templates = r.json()
        print(f"  → 共 {len(templates)} 个模板: {', '.join(t['name'] for t in templates)}")

    # 3. 知识库配置
    print("\n[3/8] 知识库配置")
    r = test("GET /api/knowledge-base/config", "GET", "/api/knowledge-base/config")
    if r:
        cfg = r.json()
        print(f"  → chunkSize={cfg.get('chunkSize')}, retrievalTopK={cfg.get('retrievalTopK')}")

    # 4. 知识库文档
    print("\n[4/8] 知识库文档列表")
    r = test("GET /api/knowledge-base/documents", "GET", "/api/knowledge-base/documents")
    if r:
        docs = r.json()
        print(f"  → 共 {len(docs)} 个文档")

    # 5. 添加知识库文档
    print("\n[5/8] 添加知识库文档")
    r = test(
        "POST /api/knowledge-base/documents",
        "POST",
        "/api/knowledge-base/documents",
        expected_status=201,
        json_data={
            "name": "后端开发面经",
            "category": "技术岗",
            "content": "Java后端开发需要掌握Spring Boot、MySQL、Redis、消息队列等技术栈。",
        },
    )
    doc_id = None
    if r:
        data = r.json()
        doc_id = data.get("id")
        print(f"  → 新增文档ID: {doc_id}")

    # 6. 删除知识库文档
    print("\n[6/8] 删除知识库文档")
    if doc_id:
        test(f"DELETE /api/knowledge-base/documents/{doc_id}", "DELETE", f"/api/knowledge-base/documents/{doc_id}")
    else:
        print("  → 跳过（上一步未获取到文档ID）")

    # 7. 生成简历（不带RAG）
    print("\n[7/8] 生成简历（不带RAG）")
    r = test(
        "POST /api/generate-resume",
        "POST",
        "/api/generate-resume",
        json_data={
            "name": "张三",
            "gender": "男",
            "age": "22",
            "phone": "13800138000",
            "email": "zhangsan@example.com",
            "school": "某某大学",
            "major": "计算机科学与技术",
            "degree": "本科",
            "politicalStatus": "共青团员",
            "applicationPosition": "Java后端开发",
            "targetRole": "后端开发工程师",
            "targetIndustry": "互联网",
            "ranking": "前10%",
            "courses": "数据结构,算法设计,操作系统,计算机网络",
            "skillsText": "Java\nSpring Boot\nMySQL\nRedis\nLinux",
            "honorsText": "国家奖学金\nACM铜奖",
            "interests": "开源贡献,技术博客",
            "selfIntroduction": "热爱编程，喜欢钻研新技术",
            "templateId": "tech-rag",
            "enableRag": False,
            "educationExperiences": [
                {
                    "school": "某某大学",
                    "degree": "本科",
                    "major": "计算机科学与技术",
                    "startDate": "2021-09",
                    "endDate": "2025-06",
                }
            ],
            "workExperiences": [],
            "projectExperiences": [
                {
                    "projectName": "校园二手交易平台",
                    "role": "后端负责人",
                    "startDate": "2023-03",
                    "endDate": "2023-06",
                    "briefIntroduction": "基于Spring Boot的校园二手交易系统",
                    "description": "负责后端架构设计与核心模块开发\n实现用户认证、商品管理、订单系统",
                }
            ],
        },
    )
    if r:
        data = r.json()
        meta = data.get("meta", {})
        resume = data.get("resumeData", {})
        print(f"  → provider: {meta.get('provider')}")
        print(f"  → template: {meta.get('templateName')}")
        print(f"  → education: {len(resume.get('education', []))} 条")
        print(f"  → skills: {len(resume.get('skills', []))} 条")
        print(f"  → projects: {len(resume.get('projects', []))} 条")
        print(f"  → summary前30字: {resume.get('summary', '')[:30]}...")

    # 8. 生成简历（带RAG）
    print("\n[8/8] 生成简历（带RAG）")
    r = test(
        "POST /api/generate-resume",
        "POST",
        "/api/generate-resume",
        json_data={
            "name": "李四",
            "gender": "女",
            "age": "23",
            "phone": "13900139000",
            "email": "lisi@example.com",
            "school": "某某大学",
            "major": "软件工程",
            "degree": "本科",
            "applicationPosition": "后端开发",
            "targetRole": "后端开发工程师",
            "skillsText": "Go\nGin\nPostgreSQL\nDocker",
            "templateId": "tech-rag",
            "enableRag": True,
            "educationExperiences": [
                {
                    "school": "某某大学",
                    "degree": "本科",
                    "major": "软件工程",
                    "startDate": "2020-09",
                    "endDate": "2024-06",
                }
            ],
            "workExperiences": [],
            "projectExperiences": [],
        },
    )
    if r:
        data = r.json()
        meta = data.get("meta", {})
        print(f"  → provider: {meta.get('provider')}")
        print(f"  → knowledgeHits: {len(meta.get('knowledgeHits', []))} 条")
        summary = data.get("resumeData", {}).get("summary", "")
        print(f"  → summary前30字: {summary[:30]}...")

    # 汇总
    print("\n" + "=" * 50)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 50)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
