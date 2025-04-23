import tkinter as tk
from tkinter import ttk
import json
import os

class MahjongAI:
    def __init__(self):
        # 初始化知识库
        self.tile_types = ['万', '条', '筒']  # 牌的类型
        self.all_tiles = [f"{num}{type}" for type in self.tile_types for num in range(1, 10)] * 4  # 所有牌
        self.discard_pile = []  # 其余三家打出的牌
        self.my_discards = []  # 自己已打出的牌
        self.my_hand = []  # 当前手牌
        self.new_tile = None  # 刚摸到的牌
        self.last_discarded_tile = None  # 记录最后打出的牌

        # 初始权重系统
        self.tile_weights = {
            f"{num}{type}": self._get_initial_weight(num)
            for type in self.tile_types
            for num in range(1, 10)
        }

        # 位置权重
        self.position_weights = {1: -2, 2: -1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: -1, 9: -2}

        # 风险评估系数
        self.risk_factors = {
            "be_eaten": 2,
            "be_ponged": {
                0: 8,
                1: 4,
                2: 0
            },
            "be_konged": 4,
            "be_winning_tile": 10,
            "already_discarded": -5
        }

        # 价值评估系数
        self.value_factors = {
            "four_of_a_kind": 20,  # 四张相同牌的系数
            "three_of_a_kind": 15,  # 三张相同牌的系数
            "pair": 10,  # 对子的系数
            "sequence": 5,  # 顺子的系数
            "single": 1  # 单牌的系数
        }

        # 加载保存的权重
        self._load_weights()

    def _get_initial_weight(self, num):
        """获取初始权重，综合考虑数字因素"""
        if num in [1, 9]:
            return 0.8
        elif num in [2, 8]:
            return 0.9
        elif num in [3, 7]:
            return 1.2
        else:  # 4,5,6
            return 1.5

    def _load_weights(self):
        """从文件加载保存的权重"""
        file_path = "mahjong_weights.json"
        if not os.path.exists(file_path):
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.tile_weights = data.get('tile_weights', self.tile_weights)
                self.position_weights = data.get('position_weights', self.position_weights)
                self.risk_factors = data.get('risk_factors', self.risk_factors)
                self.value_factors = data.get('value_factors', self.value_factors)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"加载权重文件时出错，将使用默认权重: {e}")

    def _save_weights(self):
        """保存权重到文件"""
        file_path = "mahjong_weights.json"
        data = {
            "tile_weights": self.tile_weights,
            "position_weights": self.position_weights,
            "risk_factors": self.risk_factors,
            "value_factors": self.value_factors
        }
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存权重文件时出错: {e}")

    def update_state(self, discard_pile, my_discards, my_hand, new_tile):
        """更新游戏状态"""
        self.discard_pile = discard_pile
        self.my_discards = my_discards
        self.my_hand = my_hand
        self.new_tile = new_tile
        if new_tile:
            self.my_hand.append(new_tile)  # 将新摸到的牌加入手牌

    def evaluate_tile_value(self, tile):
        """评估单张牌的价值（使用可调整的系数）"""
        count = self.my_hand.count(tile)
        positional_weight = self.get_positional_weight(tile)
        remaining_weight = self.get_remaining_weight(tile)

        # 合并后的权重
        combined_weight = self.tile_weights[tile] + remaining_weight

        if count == 4:  # 如果有四张相同的牌，可能是杠的一部分
            return (self.value_factors["four_of_a_kind"] * combined_weight) + positional_weight
        elif count == 3:  # 如果有三张相同的牌，可能是刻子的一部分
            return (self.value_factors["three_of_a_kind"] * combined_weight) + positional_weight
        elif count == 2:  # 如果有两张相同的牌，可能是对子的一部分
            return (self.value_factors["pair"] * combined_weight) + positional_weight
        elif self.is_part_of_sequence(tile):  # 如果能形成顺子
            return (self.value_factors["sequence"] * combined_weight) + positional_weight
        else:
            return (self.value_factors["single"] * combined_weight) + positional_weight

    def get_positional_weight(self, tile):
        """计算位置权重"""
        num = int(tile[:-1])
        return self.position_weights.get(num, 0)

    def get_remaining_weight(self, tile):
        """计算剩余牌权重"""
        discard_count = self.discard_pile.count(tile)
        if discard_count == 0:
            return -5
        elif discard_count == 1:
            return -2
        elif discard_count == 2:
            return 0
        else:
            return 0

    def is_part_of_sequence(self, tile):
        """判断一张牌是否能形成顺子"""
        num, type = int(tile[:-1]), tile[-1]
        for offset in [-1, 0, 1]:
            adjacent_tile = f"{num + offset}{type}"
            if adjacent_tile in self.my_hand and adjacent_tile != tile:
                return True
        return False

    def evaluate_tile_risk(self, tile):
        """评估单张牌的风险（包括被吃、碰、杠和放炮）"""
        risk = 0
        num, type = int(tile[:-1]), tile[-1]

        # 风险1：被下家吃的概率
        for offset in [-1, 0, 1]:
            adjacent_tile = f"{num + offset}{type}"
            if adjacent_tile in self.discard_pile:
                risk += self.risk_factors["be_eaten"]

        # 风险2：被碰的概率
        discard_count = self.discard_pile.count(tile)
        risk += self.risk_factors["be_ponged"].get(discard_count, 0)

        # 风险3：被杠的概率
        if discard_count == 0:
            risk += self.risk_factors["be_konged"]

        # 风险4：放炮的概率
        if self.is_potential_win_tile(tile):
            risk += self.risk_factors["be_winning_tile"]

        # 风险5：如果该牌已经在自己的弃牌堆中
        if tile in self.my_discards:
            risk += self.risk_factors["already_discarded"]

        # 根据当前风险值微调风险系数
        self._adjust_risk_factors(risk)

        return max(risk, 0)

    def _adjust_risk_factors(self, risk):
        """根据当前风险值微调风险系数"""
        if risk > 10:
            for key in self.risk_factors:
                if isinstance(self.risk_factors[key], dict):
                    for sub_key in self.risk_factors[key]:
                        self.risk_factors[key][sub_key] *= 1.1
                else:
                    self.risk_factors[key] *= 1.1
        elif risk < 5:
            for key in self.risk_factors:
                if isinstance(self.risk_factors[key], dict):
                    for sub_key in self.risk_factors[key]:
                        self.risk_factors[key][sub_key] *= 0.9
                else:
                    self.risk_factors[key] *= 0.9

        # 确保系数在合理范围内
        self.risk_factors["be_eaten"] = max(-10, min(self.risk_factors["be_eaten"], 20))
        for sub_key in self.risk_factors["be_ponged"]:
            self.risk_factors["be_ponged"][sub_key] = max(-10, min(self.risk_factors["be_ponged"][sub_key], 20))
        self.risk_factors["be_konged"] = max(-10, min(self.risk_factors["be_konged"], 20))
        self.risk_factors["be_winning_tile"] = max(-10, min(self.risk_factors["be_winning_tile"], 20))
        self.risk_factors["already_discarded"] = max(-10, min(self.risk_factors["already_discarded"], 20))

        self._save_weights()

    def is_potential_win_tile(self, tile):
        num, type = int(tile[:-1]), tile[-1]
        if self.discard_pile.count(tile) >= 2:
            return True
        for offset in [-2, -1, 1, 2]:
            adjacent_tile = f"{num + offset}{type}"
            if adjacent_tile in self.discard_pile:
                return True
        return False

    def choose_tile_to_discard(self):
        """选择要打出的牌"""
        candidates = []
        for tile in self.my_hand:
            value = self.evaluate_tile_value(tile)
            risk = self.evaluate_tile_risk(tile)
            score = value - risk
            candidates.append((tile, score))

        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]

    def play(self, discard_pile, my_discards, my_hand, new_tile):
        """主函数：根据输入选择最优出牌"""
        self.update_state(discard_pile, my_discards, my_hand, new_tile)
        tile_to_discard = self.choose_tile_to_discard()
        self.my_hand.remove(tile_to_discard)
        self.my_discards.append(tile_to_discard)
        self.last_discarded_tile = tile_to_discard
        return tile_to_discard

    def update_experience(self, is_winning):
        """根据胡牌结果更新所有相关经验因子"""
        if not self.last_discarded_tile:
            return

        tile = self.last_discarded_tile
        num = int(tile[:-1])

        # 更新价值评估系数
        if is_winning:
            # 增加最后打出的牌相关组合的权重
            count = self.my_hand.count(tile) + 1  # +1因为已经打出了

            if count >= 4:
                self.value_factors["four_of_a_kind"] *= 1.1
            if count >= 3:
                self.value_factors["three_of_a_kind"] *= 1.1
            if count >= 2:
                self.value_factors["pair"] *= 1.1
            if self.is_part_of_sequence(tile):
                self.value_factors["sequence"] *= 1.1
        else:
            # 减少最后打出的牌相关组合的权重
            count = self.my_hand.count(tile) + 1

            if count >= 4:
                self.value_factors["four_of_a_kind"] *= 0.9
            if count >= 3:
                self.value_factors["three_of_a_kind"] *= 0.9
            if count >= 2:
                self.value_factors["pair"] *= 0.9
            if self.is_part_of_sequence(tile):
                self.value_factors["sequence"] *= 0.9

        # 确保系数在合理范围内
        for key in self.value_factors:
            self.value_factors[key] = max(0.5, min(self.value_factors[key], 3.0))

        # 更新单牌权重
        if is_winning:
            self.tile_weights[tile] *= 1.2
            for offset in [-1, 0, 1]:
                adjacent_num = num + offset
                if 1 <= adjacent_num <= 9:
                    adjacent_tile = f"{adjacent_num}{tile[-1]}"
                    if adjacent_tile in self.tile_weights:
                        self.tile_weights[adjacent_tile] *= 1.1
        else:
            self.tile_weights[tile] *= 0.8
            for offset in [-1, 0, 1]:
                adjacent_num = num + offset
                if 1 <= adjacent_num <= 9:
                    adjacent_tile = f"{adjacent_num}{tile[-1]}"
                    if adjacent_tile in self.tile_weights:
                        self.tile_weights[adjacent_tile] *= 0.9

        # 更新位置权重
        if is_winning:
            self.position_weights[num] = self.position_weights.get(num, 0) * 1.1
        else:
            self.position_weights[num] = self.position_weights.get(num, 0) * 0.9

        # 更新风险评估系数
        if is_winning:
            for key in self.risk_factors:
                if isinstance(self.risk_factors[key], dict):
                    for sub_key in self.risk_factors[key]:
                        self.risk_factors[key][sub_key] *= 0.9
                else:
                    self.risk_factors[key] *= 0.9
        else:
            for key in self.risk_factors:
                if isinstance(self.risk_factors[key], dict):
                    for sub_key in self.risk_factors[key]:
                        self.risk_factors[key][sub_key] *= 1.1
                else:
                    self.risk_factors[key] *= 1.1

        # 确保权重不会超出合理范围
        self.tile_weights[tile] = max(0.5, min(self.tile_weights[tile], 2.0))
        self.position_weights[num] = max(-3, min(self.position_weights[num], 3))
        for key in self.risk_factors:
            if isinstance(self.risk_factors[key], dict):
                for sub_key in self.risk_factors[key]:
                    self.risk_factors[key][sub_key] = max(-10, min(self.risk_factors[key][sub_key], 20))
            else:
                self.risk_factors[key] = max(-10, min(self.risk_factors[key], 20))

        # 保存更新后的权重
        self._save_weights()


class MahjongApp:
    def __init__(self, root):
        self.root = root
        self.root.title("麻将 AI 策略系统")
        self.ai = MahjongAI()
        self.create_widgets()

    def create_widgets(self):
        # 标题
        title_label = tk.Label(self.root, text="麻将 AI 出牌策略", font=("Arial", 16))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # 输入：当前手牌
        tk.Label(self.root, text="当前手牌 (逗号分隔):").grid(row=1, column=0, sticky="w")
        self.hand_entry = tk.Entry(self.root, width=50)
        self.hand_entry.grid(row=1, column=1, columnspan=2, padx=10, pady=5)

        # 输入：新摸到的牌
        tk.Label(self.root, text="新摸到的牌:").grid(row=2, column=0, sticky="w")
        self.new_tile_entry = tk.Entry(self.root, width=50)
        self.new_tile_entry.grid(row=2, column=1, columnspan=2, padx=10, pady=5)

        # 输入：弃牌堆
        tk.Label(self.root, text="弃牌堆 (逗号分隔):").grid(row=3, column=0, sticky="w")
        self.discard_pile_entry = tk.Entry(self.root, width=50)
        self.discard_pile_entry.grid(row=3, column=1, columnspan=2, padx=10, pady=5)

        # 输入：自己已打出的牌
        tk.Label(self.root, text="自己已打出的牌 (逗号分隔):").grid(row=4, column=0, sticky="w")
        self.my_discards_entry = tk.Entry(self.root, width=50)
        self.my_discards_entry.grid(row=4, column=1, columnspan=2, padx=10, pady=5)

        # 按钮
        run_button = tk.Button(self.root, text="选择出牌", command=self.run_ai)
        run_button.grid(row=5, column=0, pady=10)
        win_button = tk.Button(self.root, text="本轮胡牌", command=self.mark_winning)
        win_button.grid(row=5, column=1, pady=10)
        lose_button = tk.Button(self.root, text="本轮未胡牌", command=self.mark_losing)
        lose_button.grid(row=5, column=2, pady=10)

        # 输出
        tk.Label(self.root, text="AI 建议出牌:").grid(row=6, column=0, sticky="w")
        self.result_label = tk.Label(self.root, text="", font=("Arial", 14), fg="blue")
        self.result_label.grid(row=6, column=1, columnspan=2, padx=10, pady=5)

        # 权重显示区域
        tk.Label(self.root, text="当前权重:").grid(row=7, column=0, sticky="w")
        self.weights_text = tk.Text(self.root, height=10, width=60)
        self.weights_text.grid(row=8, column=0, columnspan=3, padx=10, pady=5)
        self.update_weights_display()

    def sort_hand(self, hand):
        """对手牌进行排序"""
        tile_order = {'万': 0, '条': 1, '筒': 2}
        return sorted(hand, key=lambda tile: (tile_order[tile[-1]], int(tile[:-1])))

    def run_ai(self):
        """运行 AI 并显示结果"""
        try:
            hand = [tile.strip() for tile in self.hand_entry.get().split(",") if tile.strip()]
            new_tile = self.new_tile_entry.get().strip()
            discard_pile = [tile.strip() for tile in self.discard_pile_entry.get().split(",") if tile.strip()]
            my_discards = [tile.strip() for tile in self.my_discards_entry.get().split(",") if tile.strip()]

            tile_to_discard = self.ai.play(discard_pile, my_discards, hand, new_tile)
            self.result_label.config(text=tile_to_discard)

            remaining_hand = self.ai.my_hand[:]
            sorted_hand = self.sort_hand(remaining_hand)
            self.hand_entry.delete(0, tk.END)
            self.hand_entry.insert(0, ", ".join(sorted_hand))

            updated_discards = self.ai.my_discards[:]
            self.my_discards_entry.delete(0, tk.END)
            self.my_discards_entry.insert(0, ", ".join(updated_discards))

            self.update_weights_display()
        except Exception as e:
            self.result_label.config(text=f"错误: {str(e)}")

    def mark_winning(self):
        """标记本轮胡牌"""
        try:
            self.ai.update_experience(is_winning=True)
            self.result_label.config(text="已标记胡牌，更新相关权重！")
            self.update_weights_display()
        except Exception as e:
            self.result_label.config(text=f"错误: {str(e)}")

    def mark_losing(self):
        """标记本轮未胡牌"""
        try:
            self.ai.update_experience(is_winning=False)
            self.result_label.config(text="已标记未胡牌，更新相关权重！")
            self.update_weights_display()
        except Exception as e:
            self.result_label.config(text=f"错误: {str(e)}")

    def update_weights_display(self):
        """更新权重显示区域"""
        weights_text = "当前权重设置:\n"
        weights_text += f"位置权重: {self.ai.position_weights}\n"
        weights_text += f"价值评估系数: {self.ai.value_factors}\n"
        weights_text += f"风险评估系数: {self.ai.risk_factors}\n"

        if self.ai.last_discarded_tile:
            tile = self.ai.last_discarded_tile
            weights_text += f"\n最后打出的牌 '{tile}' 的权重: {self.ai.tile_weights.get(tile, 1.0):.2f}\n"
            weights_text += f"相邻牌权重: "
            num = int(tile[:-1])
            for offset in [-1, 0, 1]:
                adjacent_num = num + offset
                if 1 <= adjacent_num <= 9:
                    adjacent_tile = f"{adjacent_num}{tile[-1]}"
                    weights_text += f"{adjacent_tile}:{self.ai.tile_weights.get(adjacent_tile, 1.0):.2f} "
        else:
            weights_text += "\n暂无最后打出的牌信息。\n"

        self.weights_text.delete(1.0, tk.END)
        self.weights_text.insert(tk.END, weights_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = MahjongApp(root)
    root.mainloop()