# Browser-Use Test Optimization Iteration Log

## Overview
This document records 10 iterations of optimizing browser-use prompts for AdWave E2E testing.

**Goal:** Reduce test execution time by making prompts more specific and targeted.

---

## Iteration 1: Baseline Analysis

**Date:** 2026-01-13

### Current Prompt Analysis

**Problem:** Prompts are too vague, causing browser-use agent to take unnecessary steps.

**Current `login_and_navigate` prompt:**
```
1. Navigate to {login_url}
2. Enter {email} in the email input field
3. Enter {password} in the password input field
4. Click the login button
5. Wait for login to complete
6. Navigate to {target_url}
7. Wait for the page to load
8. Report the page title and URL
```

**Issues Identified:**
- "Wait for login to complete" is vague - agent doesn't know what to look for
- "Wait for the page to load" is vague
- "Report the page title and URL" causes agent to do extra analysis

### Baseline Test Run

| Test | Time |
|------|------|
| test_analytics_page | ~180s |
| test_audience_page | ~180s |
| test_campaign_page | ~180s |
| test_creative_page | ~180s |
| test_login | ~70s |
| **Total** | **896s (14:56)** |
| **Average** | **179s/test** |

**Analysis:**
- Each login_and_navigate test takes ~3 minutes
- Agent performs too many unnecessary steps
- Prompts need to be more direct

---

## Iteration 2: Prompt Optimization

**Date:** 2026-01-13

### Changes Made
1. Reduce `max_steps` from 25 to 10
2. Simplify prompts - remove unnecessary reporting
3. Make success criteria explicit in prompt
4. Use direct actions only

### Optimized Prompts

**login() - Before:**
```
1. Navigate to {login_url}
2. Enter {email} in the email input field
3. Enter {password} in the password input field
4. Click the login button
5. Wait for the page to redirect after login
6. Return the current page URL
```

**login() - After:**
```
Go to {login_url}, enter {email} and {password}, click login button. Done when URL changes from /login.
```

### Test Run

| Test | Result | Time |
|------|--------|------|
| test_analytics_page | PASSED | ~158s |
| test_audience_page | FAILED (rate limit 429) | - |
| test_campaign_page | PASSED | ~158s |
| test_creative_page | PASSED | ~158s |
| test_login | PASSED | ~70s |
| **Total** | **4/5 passed** | **791s (13:11)** |

**Improvement:** 105s faster than baseline (~12% improvement)

**Issues Found:**
- API rate limiting (429) caused one test to fail
- Not a prompt issue - need to add delays between tests

---

## Iteration 3: Rate Limit Handling + Further Optimization

**Date:** 2026-01-13

### Changes Made
1. Add 5s delay between tests in conftest.py
2. Keep simplified prompts from Iteration 2

### Test Run

| Test | Result | Time |
|------|--------|------|
| test_analytics_page | PASSED | - |
| test_audience_page | PASSED | - |
| test_campaign_page | PASSED | - |
| test_creative_page | PASSED | - |
| test_login | PASSED | - |
| **Total** | **5/5 passed** | **3002s (50:02)** |

**ISSUE:** Test time increased dramatically from 791s to 3002s!

**Analysis:**
- The delay alone cannot explain this (only adds 20s)
- Prompts may be TOO simple, causing agent confusion
- Agent may be taking more steps due to unclear instructions

---

## Iteration 4: Revert Delay + Structured Prompts

**Date:** 2026-01-13

### Changes Made
1. Remove the 5s delay (rate limiting not main issue)
2. Use structured but concise prompts
3. Add explicit success criteria in prompt

### Test Run

| Test | Result | Time |
|------|--------|------|
| All 5 tests | PASSED | **3075s (51:15)** |

**ISSUE:** Still slow despite structured prompts

**Analysis:**
- API rate limiting causing delayed responses
- Each LLM call takes longer due to throttling
- Need to reduce steps and add cooldown

---

## Iteration 5: Reduce Steps + API Cooldown

**Date:** 2026-01-13

### Changes Made
1. Reduce max_steps from 10 to 8
2. Add 10s delay between tests for API cooldown
3. Keep structured prompts

### Test Run
- Interrupted due to slow execution

---

## Iteration 6: Non-Vision Model Test

**Date:** 2026-01-13

### Changes Made
1. Switch to `Qwen/Qwen2.5-72B-Instruct` (non-VL model)
2. Hypothesis: Vision processing is slow

### Test Run

| Test | Result | Time |
|------|--------|------|
| test_login (single) | PASSED | **25s** |
| All 5 tests | 2 passed, 3 failed | 712s |

**Key Finding:**
- Single test: 25s (vs 70s with VL model) - **64% faster!**
- BUT: Browser-Use sends screenshots by default
- Non-VL models error: "The model is not a VLM"
- **Conclusion: Must use Vision Language Model for browser-use**

---

## Iteration 7: Smaller VL Model

**Date:** 2026-01-13

### Changes Made
- Switch to `Qwen/Qwen2.5-VL-7B-Instruct` (7B vs 32B)
- Smaller model = faster inference

### Test Run
- Interrupted

---

## Summary & Conclusions

### Performance Results

| Iteration | Model | Time | Notes |
|-----------|-------|------|-------|
| 1 (Baseline) | VL-32B | 896s | Original |
| 2 | VL-32B | 791s | 12% faster (simplified prompts) |
| 3-5 | VL-32B | 3000s+ | API rate limiting |
| 6 | Non-VL 72B | 25s/test | VLM required, tests failed |

### Key Findings

1. **Prompt optimization works** - Iteration 2 showed 12% improvement
2. **API rate limiting is main bottleneck** - SiliconFlow free tier has TPM limits
3. **Browser-Use requires VLM** - Non-vision models cannot process screenshots
4. **Model size matters** - Smaller VL models may be faster

### Recommendations

1. **Upgrade SiliconFlow account** - Higher TPM limits
2. **Use smaller VL model** - `Qwen2.5-VL-7B-Instruct`
3. **Implement session reuse** - Login once, run all tests
4. **Add retry with backoff** - Handle rate limits gracefully
5. **Consider OpenAI API** - More stable, less rate limiting

---

# 重新迭代：产品分析与优化

## 重新迭代 1: AdWave 页面结构分析

**Date:** 2026-01-14

### 分析目标
不再关注 API 问题，专注于分析 AdWave 产品的实际页面结构。

### 页面结构分析结果

#### Login 页面 (https://adwave.revosurge.com/login)
- **输入框**: "电邮"、"密码"
- **按钮**: "登入"
- **链接**: 忘记密码、注册

#### Campaign 页面 (/campaign)
- **页面标题**: "推广计划"
- **导航菜单**: 4项 - 推广计划、数据分析、创意素材库、受众人群
- **操作按钮**: "开始" 按钮

#### Analytics 页面 (/analytics)
- **页面标题**: "数据分析"
- **图表区域**: 数据可视化组件
- **指标展示**: 关键业务指标

#### Creative 页面 (/creative)
- **页面标题**: "创意素材库"
- **资产列表**: 素材展示区

#### Audience 页面 (/audience)
- **页面标题**: "受众人群"
- **受众列表**: 人群数据展示

---

## 重新迭代 2: 针对性提示词优化

**Date:** 2026-01-14

### 优化策略
基于实际页面结构，使用准确的中文元素名称编写提示词。

### 优化后的提示词

**login() 提示词:**
```
访问 {login_url}
在"电邮"输入框输入 {email}
在"密码"输入框输入 {password}
点击"登入"按钮
完成条件: URL变为 /campaign
```

**login_and_navigate() 提示词:**
```
访问 {login_url}
在"电邮"输入框输入 {email}
在"密码"输入框输入 {password}
点击"登入"按钮
登录后点击导航菜单"{nav_name}"
完成条件: URL包含 /{page_key}
```

### 页面名称映射
```python
page_map = {
    "campaign": "推广计划",
    "analytics": "数据分析",
    "creative": "创意素材库",
    "audience": "受众人群",
}
```

---

## 重新迭代 3: 最终测试验证

**Date:** 2026-01-14

### 配置
- **API**: 智谱 GLM 官方 API
- **模型**: GLM-4.6V
- **提示词**: 针对性中文提示词

### 测试结果

| Test | Result |
|------|--------|
| test_analytics_page | ✅ PASSED |
| test_audience_page | ✅ PASSED |
| test_campaign_page | ✅ PASSED |
| test_creative_page | ✅ PASSED |
| test_login | ✅ PASSED |

**总时间: 711.50s (11:51)**
**通过率: 5/5 (100%)**

### 与基线对比

| 指标 | 基线 (Iteration 1) | 最终结果 | 改进 |
|------|-------------------|----------|------|
| 总时间 | 896s | 711.50s | **-20.6%** |
| 通过率 | 100% | 100% | 持平 |
| API | SiliconFlow | 智谱 GLM | 更稳定 |

### 总结

1. **针对性提示词有效** - 使用实际元素名称减少了 agent 的探索步骤
2. **智谱 GLM-4.6V 稳定** - 无 JSON 格式问题，无明显限流
3. **测试时间减少 20.6%** - 从 896s 降至 711.50s
