# Sweekar - AI 口袋宠物

本地运行的 AI 陪伴宠物原型，具备记忆进化功能。

## 功能特性

- **宠物命名**: 首次运行时为宠物起名
- **聊天界面**: 与宠物进行交互对话
- **宠物状态**: 心情、饥饿度、健康值追踪
- **记忆系统**: 短时记忆 + 长时记忆 + 用户画像自动提取
- **数据持久化**: 所有数据本地存储（JSON/CSV）

## 项目结构

```
sweekar/
├── app.py                      # Streamlit 主界面入口
├── chat/
│   └── chat_engine.py          # 聊天处理 + JSONL 追加写入
├── memory/
│   ├── memory_pipeline.py      # 高级记忆管道（整合自 demo_sweekar1.0）
│   └── run_daily_update.py     # 定时记忆更新调度器
├── config/
│   └── pet_config.py           # 宠物配置与状态管理
├── storage/                    # 数据存储目录
│   ├── conversation.jsonl      # 聊天记录（append-safe）
│   ├── short_memory.json      # 短时记忆（评分驱动）
│   ├── long_memory.json       # 长时记忆
│   ├── profile_events.csv      # 原始事件（append-only）
│   └── profile_traits.csv     # 用户特质（带强度衰减）
└── config/
    ├── pet_config.json         # 宠物名称设置
    └── pet_state.json         # 当前宠物状态
```

## 安装依赖

```bash
pip install streamlit apscheduler
```

## 运行应用

```bash
cd swekar
streamlit run app.py
```

浏览器会自动打开 http://localhost:8501

## 运行记忆调度器

### 方式一：后台持续运行（每24小时自动更新）

```bash
python -m memory.run_daily_update
```

### 方式二：手动触发一次更新

```bash
python -m memory.run_daily_update --once
```

### 方式三：自定义更新间隔

```bash
python -m memory.run_daily_update --interval 12
```

## 记忆系统说明

### 评分驱动淘汰（Eviction）

当短时记忆容量达到 50 上限时，会根据评分淘汰最低分记忆：

```
score = 0.5 × recency + 0.3 × importance + 0.2 × (access_count / 10)
```

- **recency**: 时间衰减，7天完全衰减
- **importance**: 按事件类型赋值（情绪 0.8 > 关系 0.9 > 目标 0.7 > 偏好 0.5 > 事实 0.4）
- **access_count**: 每次检索时 +1

### 短时记忆 → 长时记忆晋升

满足以下条件时自动晋升：
- `score > 0.2` AND `access_count > 2`
- 或者同一事件在7天内出现 2 次以上

### 特质强度衰减

每次新证据更新特质时：

```
new_strength = old_strength × 0.8 + signal × 0.2
```

- 强度 > 0.7 → stable（稳定）
- 强度 > 0.4 → developing（发展中）
- 强度 ≤ 0.4 → emerging（萌芽）

### 长时记忆检索衰减

如果 30 天内未被检索，`retrieval_count` 自动 -1

## 数据存储位置

| 文件 | 说明 |
|------|------|
| `storage/conversation.jsonl` | 所有聊天记录（只追加） |
| `storage/short_memory.json` | 短时记忆（最近50条） |
| `storage/long_memory.json` | 长时记忆（晋升的记忆） |
| `storage/profile_events.csv` | 原始事件（append-only） |
| `storage/profile_traits.csv` | 用户特质（强度衰减） |
| `config/pet_config.json` | 宠物名称和设置 |
| `config/pet_state.json` | 当前宠物状态 |

## 记忆更新流程

1. 读取近 7 天对话（conversation.jsonl）
2. 提取事件、情绪、偏好（关键词匹配）
3. 更新短时记忆（评分 + 淘汰）
4. 检查重复事件 → 晋升到长时记忆
5. 更新用户特质（强度更新）
6. 应用时间衰减
7. 持久化到所有存储文件

## 调度器说明

`run_daily_update.py` 是独立模块，可以：
- 作为后台进程持续运行（APScheduler）
- 手动触发一次（--once）
- 不依赖于主 UI 进程

建议和主应用同时运行，确保记忆系统持续更新。
