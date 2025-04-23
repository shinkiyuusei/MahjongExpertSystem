import tkinter as tk
from mahjong_ai import MahjongAI


class MahjongApp:
    def __init__(self, root):
        self.root = root
        self.root.title("麻将 AI 策略系统")
        self.ai = MahjongAI()
        self.create_widgets()

    def create_widgets(self):
        # 标题
        title_label = tk.Label(self.root, text="麻将出牌策略系统", font=("Arial", 16))
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
        tk.Label(self.root, text="系统建议出牌:").grid(row=6, column=0, sticky="w")
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
