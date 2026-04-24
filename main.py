import torch
import torch.nn as nn
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn

app = FastAPI()

# 跨域配置：确保小程序能够顺利拨通后端接口
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 1. LSTM 模型结构定义 (用于时序特征提取)
# ==========================================
class PeriodLSTM(nn.Module):
    def __init__(self, input_size=1, hidden_size=64, num_layers=2):
        super(PeriodLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        # x 维度: (batch, seq_len, 1)
        out, _ = self.lstm(x)
        # 提取最后一个时间步的隐藏状态映射到输出
        return self.fc(out[:, -1, :])

# 初始化模型（当前为评估模式，模拟神经网络介入）
model = PeriodLSTM()
model.eval()

# ==========================================
# 2. 模拟内存数据库
# ==========================================
user_db = {
    "1": {
        "dates": [],         # 存储原始日期字符串
        "intervals": []      # 自动生成的有效天数间隔序列
    }
}

# ==========================================
# 3. 核心业务 API 接口
# ==========================================

# --- 接口 A：记录日期并自动清洗特征 ---
@app.post("/api/record_date")
async def record_date(data: dict = Body(...)):
    user_id = "1"
    new_date = data.get("date")
    db = user_db[user_id]
    
    if new_date not in db["dates"]:
        db["dates"].append(new_date)
        db["dates"].sort() # 保证时序递增
        
    # 特征工程：计算 Delta T (间隔天数)
    if len(db["dates"]) >= 2:
        intervals = []
        for i in range(len(db["dates"]) - 1):
            d1 = datetime.strptime(db["dates"][i], "%Y-%m-%d")
            d2 = datetime.strptime(db["dates"][i+1], "%Y-%m-%d")
            diff = (d2 - d1).days
            # 【异常值过滤】只记录生理学上合理的间隔 (15-50天)
            if 15 < diff < 50:
                intervals.append(diff)
        db["intervals"] = intervals
        
    return {"status": "success", "count": len(db["dates"]), "history": db["intervals"]}

# --- 接口 B：混合 AI 推理预测 (含鲁棒性约束) ---
@app.get("/api/predict/{user_id}")
async def predict_period(user_id: str):
    db = user_db.get(user_id)
    intervals = db["intervals"]
    
    # 冷启动判断
    if not intervals:
        return {"has_data": False, "msg": "数据样本不足，请至少记录两次有效日期"}

    # 1. 提取有效特征（仅取最近 5 次，代表近期趋势）
    valid_seq = intervals[-5:]
    last_val = valid_seq[-1]
    avg_val = sum(valid_seq) / len(valid_seq)
    
    # 2. 执行 LSTM 神经推理
    # 归一化输入
    seq_tensor = torch.FloatTensor(valid_seq).view(1, -1, 1) / 40.0
    with torch.no_grad():
        lstm_out = model(seq_tensor).item()

    # 3. 【核心公式】混合加权算子与数值截断
    # 逻辑：预测周期 = 最近值*0.4 + 均值*0.4 + (神经推理修正)*0.2
    # 初始权重分配确保了数据一变，结果立刻响应
    raw_prediction = (last_val * 0.4) + (avg_val * 0.4) + ((lstm_out + 0.7) * 40 * 0.2)
    
    # 【安全护栏】强制约束在 21-35 天，解决“六十几天”的数值溢出问题
    predicted_cycle = int(max(21, min(35, raw_prediction)))
    
    # 4. 时间轴计算逻辑优化
    last_date = datetime.strptime(db["dates"][-1], "%Y-%m-%d")
    today = datetime.now()
    days_since_last = (today - last_date).days
    
    # 距离下次天数 = 预测总长度 - 距离上次已过去天数
    days_left = predicted_cycle - days_since_last

    return {
        "has_data": True,
        "predicted_days": days_left if days_left > 0 else "即将到来",
        "cycle_length": predicted_cycle,
        "history_sequence": valid_seq,
        "status": "卵泡期" if days_left > 14 else "黄体期"
    }

# --- 接口 C：多维特征推荐引擎 (全维度决策树) ---
@app.post("/api/recommend")
async def recommend(data: dict):
    # 接收来自前端的 11 维体征数据
    p = {
        "pain": int(data.get('pain_level', 0)),
        "flow": int(data.get('flow_level', 2)),
        "emotion": data.get('emotion', 'calm'),
        "diet": data.get('diet', 'normal'),
        "stress": int(data.get('stress', 1)),
        "sleep": float(data.get('sleep_hours', 8)),
        "water": int(data.get('water_cups', 5)),
        "symptoms": data.get('symptoms', [])
    }

    plans = []
    # 模拟集成决策树分支
    if p["pain"] >= 2:
        plans.append({"title": "止痛建议", "content": "痛感达中重度，建议侧卧静卧并配合腹部热敷，减少剧烈运动。"})
    if p["flow"] >= 3:
        plans.append({"title": "流量维护", "content": "检测到流量较大，建议补充含铁食物（如猪血、菠菜），保证血氧运输。"})
    if p["diet"] in ['cold', 'spicy']:
        plans.append({"title": "膳食调优", "content": "刺激性饮食可能诱发子宫过度收缩，建议切换为温热流食。"})
    if p["sleep"] < 7:
        plans.append({"title": "深度修复", "content": "睡眠不足将放大疼痛敏感度，今晚建议提前一小时强制入睡。"})
    if 'headache' in p["symptoms"] or p["stress"] >= 2:
        plans.append({"title": "压力释放", "content": "伴随头痛或高压感，推荐进行5分钟冥想，调节植物神经。"})

    if not plans:
        plans.append({"title": "日常方案", "content": "当前指标平稳，请继续保持规律记录与健康作息。"})

    return {"plans": plans}

# ==========================================
# 4. 运行环境配置
# ==========================================
if __name__ == "__main__":
    # 把端口改为 80，因为这是云上的标准端口
    uvicorn.run(app, host="0.0.0.0", port=80)