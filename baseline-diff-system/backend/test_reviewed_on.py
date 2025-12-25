#!/usr/bin/env python3
"""
测试 Reviewed-on 字段提取
验证从 commit message 中正确提取 Reviewed-on URL
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from git_scanner import GitScanner


def test_reviewed_on_extraction():
    """测试 Reviewed-on 提取逻辑"""
    print("\n" + "=" * 70)
    print("Reviewed-on 提取测试")
    print("=" * 70)

    scanner = GitScanner(".", "test")

    test_cases = [
        {
            "name": "标准 Gerrit URL",
            "message": """Fix security issue

Some description here.

Bug: 193445603
Test: manual test
Reviewed-on: https://android-review.googlesource.com/c/platform/frameworks/base/+/123456
Change-Id: Ib2b0342af85679c0514fb4d88530376b58e6e12a""",
            "expected": "https://android-review.googlesource.com/c/platform/frameworks/base/+/123456"
        },
        {
            "name": "多个 URL（取第一个）",
            "message": """Merge commit

Reviewed-on: https://android-review.googlesource.com/c/project1/+/111111
Reviewed-on: https://android-review.googlesource.com/c/project2/+/222222
Change-Id: I12345""",
            "expected": "https://android-review.googlesource.com/c/project1/+/111111"
        },
        {
            "name": "HTTP URL",
            "message": """Test commit

Reviewed-on: http://review.example.com/12345
Change-Id: Iabc123""",
            "expected": "http://review.example.com/12345"
        },
        {
            "name": "无 Reviewed-on",
            "message": """Regular commit

Just a normal commit without review URL.
Change-Id: I99999""",
            "expected": None
        },
        {
            "name": "大小写不敏感",
            "message": """Test case sensitivity

reviewed-on: https://review.example.com/test
Change-Id: Itest""",
            "expected": "https://review.example.com/test"
        },
        {
            "name": "URL 包含特殊字符",
            "message": """Special chars in URL

Reviewed-on: https://android-review.googlesource.com/c/platform/frameworks/base/+/2345678/1
Change-Id: Ispecial""",
            "expected": "https://android-review.googlesource.com/c/platform/frameworks/base/+/2345678/1"
        }
    ]

    passed = 0
    failed = 0

    for test in test_cases:
        result = scanner.extract_reviewed_on(test['message'])
        expected = test['expected']

        if result == expected:
            print(f"\n✓ {test['name']}")
            print(f"  提取: {result}")
            passed += 1
        else:
            print(f"\n✗ {test['name']}")
            print(f"  期望: {expected}")
            print(f"  实际: {result}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 70)

    return failed == 0


def test_url_priority():
    """测试 URL 优先级逻辑"""
    print("\n" + "=" * 70)
    print("URL 优先级测试")
    print("=" * 70)

    print("""
URL 选择逻辑:
1. 如果有 Reviewed-on URL → 使用 Reviewed-on URL
2. 否则，如果有 remote_url → 使用 {remote_url}/{project}/commit/{hash}
3. 都没有 → url = None

示例:
""")

    examples = [
        {
            "scenario": "有 Reviewed-on",
            "reviewed_on": "https://android-review.googlesource.com/c/project/+/123456",
            "remote_url": "https://android.googlesource.com",
            "project": "platform/frameworks/base",
            "hash": "abc123",
            "expected": "https://android-review.googlesource.com/c/project/+/123456"
        },
        {
            "scenario": "无 Reviewed-on，有 remote_url",
            "reviewed_on": None,
            "remote_url": "https://android.googlesource.com",
            "project": "platform/frameworks/base",
            "hash": "abc123",
            "expected": "https://android.googlesource.com/platform/frameworks/base/commit/abc123"
        },
        {
            "scenario": "都没有",
            "reviewed_on": None,
            "remote_url": None,
            "project": "platform/frameworks/base",
            "hash": "abc123",
            "expected": None
        }
    ]

    for example in examples:
        print(f"\n场景: {example['scenario']}")
        print(f"  reviewed_on: {example['reviewed_on']}")
        print(f"  remote_url:  {example['remote_url']}")

        # 模拟 URL 选择逻辑
        if example['reviewed_on']:
            url = example['reviewed_on']
        elif example['remote_url']:
            url = f"{example['remote_url']}/{example['project']}/commit/{example['hash']}"
        else:
            url = None

        if url == example['expected']:
            print(f"  ✓ 结果: {url}")
        else:
            print(f"  ✗ 期望: {example['expected']}")
            print(f"  ✗ 实际: {url}")


def main():
    """主函数"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "Reviewed-on 测试" + " " * 32 + "║")
    print("╚" + "═" * 68 + "╝")

    # 测试提取逻辑
    extraction_ok = test_reviewed_on_extraction()

    # 测试 URL 优先级
    test_url_priority()

    print("\n" + "=" * 70)
    if extraction_ok:
        print("✅ 所有测试通过")
        print("\n功能说明:")
        print("  • Reviewed-on URL 会被提取并优先使用")
        print("  • 支持 HTTP 和 HTTPS")
        print("  • 大小写不敏感")
        print("  • 如果没有 Reviewed-on，回退到 hash-based URL")
    else:
        print("❌ 部分测试失败")
    print("=" * 70)

    return 0 if extraction_ok else 1


if __name__ == "__main__":
    sys.exit(main())
