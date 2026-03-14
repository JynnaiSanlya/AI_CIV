# AI Civilization Simulation Game

## 游戏概述
这是一个人工智能模拟人类文明发展的游戏，让两个AI模型控制的文明从原始时期发展到未来。

## 功能特点
- 两个AI文明相互竞争发展
- 支持阿里云百炼qwen-flash和qwen-plus模型
- 模拟文明的多个维度：资源、人口、军队、科技、忠诚度
- 自动保存游戏状态
- 详细的游戏日志和最终总结

## 配置要求
1. Python 3.8+
2. 安装依赖：`pip install -r requirements.txt`
3. 配置API密钥：在`config.json`文件中填写您的API密钥

## 如何运行
```bash
python game.py
```

## 游戏机制

### 文明属性
- **资源**：用于发展科技、建造军队和增加人口
- **人口**：影响资源生产和文明规模
- **军队**：保护文明和进行扩张
- **科技**：决定文明的发展阶段和能力
- **时代**：根据科技水平自动升级（原始→古代→中世纪→现代→未来）

### AI决策
每个文明由不同的AI模型控制，AI会根据当前文明状态和对手情况做出决策。

### 可用行动
1. **发展科技**：消耗资源提升科技水平
2. **建造军队**：消耗资源增加军事力量
3. **增长人口**：消耗资源增加人口数量
4. **收集资源**：不消耗资源，增加资源储备

## 游戏结束条件
- 达到最大回合数（默认100回合）
- 一个文明的科技水平达到100且是对手的两倍以上
- 一个文明的人口崩溃（人口≤0）
- 一个文明的忠诚度降至0

## 配置文件
在`config.json`中配置API密钥：
```json
{
    "anthropic_api_key": "your_anthropic_api_key_here",
    "openai_api_key": "your_openai_api_key_here",
    "aliyun_api_key": "your_aliyun_api_key_here",
    "aliyun_api_secret": "your_aliyun_api_secret_here"
}
```

## 使用阿里云百炼模型

### 配置阿里云API密钥
1. 登录阿里云百炼控制台，获取API密钥
2. 在`config.json`中填写`aliyun_api_key`和`aliyun_api_secret`

### 使用qwen-flash和qwen-plus
游戏默认使用阿里云的qwen-flash和qwen-plus模型。如果需要修改模型，可以在`game.py`中修改初始化参数：

```python
# 默认配置（阿里云模型）
game = CivilizationGame(
    model_name1="qwen-flash",
    model_name2="qwen-plus"
)
```

## 游戏输出
- 每回合显示两个文明的状态
- 每个文明的行动和结果
- 自动保存游戏状态到JSON文件
- 游戏结束时显示最终总结

## 自定义游戏
您可以在`game.py`中修改以下参数：
- `max_turns`：最大回合数
- 文明名称和颜色
- AI模型类型

## 技术实现
- 支持调用阿里云百炼API
- 采用面向对象的设计模式
- 支持JSON配置和状态保存

## 扩展建议
- 添加更多文明属性（文化、经济、环境等）
- 实现文明间的交互（贸易、战争、外交）
- 添加可视化界面
- 支持更多AI模型
- 实现更复杂的科技树

## 注意事项
- 游戏需要有效的API密钥才能运行
- API调用可能会产生费用
- 建议先使用少量回合进行测试

## 许可证
MIT License

## 版本更新

完整的版本更新公告请查看 `announcements` 文件夹：

- [0.1.2版本更新](announcements/0.1.2.md) (2026-03-14)
- [0.1.1版本更新](announcements/0.1.1.md) (2026-03-14)
- [0.1.0版本更新](announcements/0.1.0.md) (2026-03-14)

## 版本文件

当前版本号存储在 `version.txt` 文件中。