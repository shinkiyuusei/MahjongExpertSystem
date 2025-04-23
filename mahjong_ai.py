import json
import os

class MahjongAI:
    def __init__(self):
        # 定义麻将牌的类型，包含万、条、筒
        self.tile_types = ['万', '条', '筒']
        # 生成所有的麻将牌，每种牌有 4 张
        self.all_tiles = [f"{num}{type}" for type in self.tile_types for num in range(1, 10)] * 4
        # 公共的弃牌堆
        self.discard_pile = []
        # 自己的弃牌列表
        self.my_discards = []
        # 自己手中的牌
        self.my_hand = []
        # 新摸到的牌
        self.new_tile = None
        # 上一次打出的牌
        self.last_discarded_tile = None

        # 初始化每张牌的权重
        self.tile_weights = {
            f"{num}{type}": self._get_initial_weight(num)
            for type in self.tile_types for num in range(1, 10)
        }
        # 不同位置牌的权重
        self.position_weights = {1: -2, 2: -1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: -1, 9: -2}
        # 各种风险因素的权重
        self.risk_factors = {
            "be_eaten": 2,
            "be_ponged": {0: 8, 1: 4, 2: 0},
            "be_konged": 4,
            "be_winning_tile": 10,
            "already_discarded": -5
        }
        # 各种牌型的价值因素权重
        self.value_factors = {
            "four_of_a_kind": 20,
            "three_of_a_kind": 15,
            "pair": 10,
            "sequence": 5,
            "single": 1
        }
        # 从文件中加载权重
        self._load_weights()

    def update_experience(self, is_winning):
        """
        根据游戏是否获胜更新权重，以积累经验
        :param is_winning: 布尔值，表示游戏是否获胜
        """
        if not self.last_discarded_tile:
            return
        tile = self.last_discarded_tile
        num = int(tile[:-1])
        # 根据是否获胜确定调整因子
        factor = 1.1 if is_winning else 0.9

        print(
            f"Before update: tile_weights={self.tile_weights}, position_weights={self.position_weights}, risk_factors={self.risk_factors}, value_factors={self.value_factors}")

        # 更新价值因素权重
        self._update_value_factors(tile, factor)
        # 更新牌的权重
        self._update_tile_weights(tile, num, factor)
        # 更新位置权重
        self._update_position_weights(num, factor)
        # 更新风险因素权重
        self._update_risk_factors(factor)

        # 保存更新后的权重到文件
        self._save_weights()
        print(
            f"After update: tile_weights={self.tile_weights}, position_weights={self.position_weights}, risk_factors={self.risk_factors}, value_factors={self.value_factors}")

    def _get_initial_weight(self, num):
        """
        根据牌的数字获取初始权重
        :param num: 牌的数字
        :return: 初始权重
        """
        if num in [1, 9]:
            return 0.8
        elif num in [2, 8]:
            return 0.9
        elif num in [3, 7]:
            return 1.2
        return 1.5

    def _load_weights(self):
        """
        从文件中加载权重，如果文件不存在或解析出错则使用默认权重
        """
        file_path = "mahjong_weights.json"
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    self.tile_weights = data.get('tile_weights', self.tile_weights)
                    self.position_weights = data.get('position_weights', self.position_weights)
                    self.risk_factors = data.get('risk_factors', self.risk_factors)
                    self.value_factors = data.get('value_factors', self.value_factors)
            except (json.JSONDecodeError, FileNotFoundError):
                print("加载权重文件时出错，将使用默认权重。")

    def _save_weights(self):
        """
        将当前的权重保存到文件中
        """
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
        except Exception:
            print("保存权重文件时出错。")

    def update_state(self, discard_pile, my_discards, my_hand, new_tile):
        """
        更新游戏状态
        """
        self.discard_pile = discard_pile
        self.my_discards = my_discards
        self.my_hand = my_hand
        self.new_tile = new_tile
        if new_tile:
            self.my_hand.append(new_tile)

    def evaluate_tile_value(self, tile):
        """
        评估一张牌的价值
        """
        count = self.my_hand.count(tile)#牌的数量
        combined_weight = self.tile_weights[tile] + self.get_remaining_weight(tile)#牌的权重
        value = self._get_value_based_on_count(count, combined_weight, tile)#牌的价值
        return value + self.get_positional_weight(tile)#牌的位置权重

    def _get_value_based_on_count(self, count, combined_weight, tile=None):
        """
        根据牌的数量和组合权重计算牌的价值
        """
        if count == 4:
            return self.value_factors["four_of_a_kind"] * combined_weight
        elif count == 3:
            return self.value_factors["three_of_a_kind"] * combined_weight
        elif count == 2:
            return self.value_factors["pair"] * combined_weight
        elif tile and self.is_part_of_sequence(tile):
            return self.value_factors["sequence"] * combined_weight
        return self.value_factors["single"] * combined_weight

    def get_positional_weight(self, tile):
        """
        获取牌的位置权重
        """
        num = int(tile[:-1])
        return self.position_weights.get(num, 0)

    def get_remaining_weight(self, tile):
        """
        根据公共弃牌堆中牌的数量获取剩余权重
        """
        discard_count = self.discard_pile.count(tile)
        return {-5: 0, -2: 1}.get(discard_count, 0)

    def is_part_of_sequence(self, tile):
        """
        判断一张牌是否是顺子的一部分
        """
        num, type = int(tile[:-1]), tile[-1]
        return any(f"{num + offset}{type}" in self.my_hand and f"{num + offset}{type}" != tile for offset in [-1, 0, 1])

    def evaluate_tile_risk(self, tile):
        num, type = int(tile[:-1]), tile[-1]
        risk = 0
        # 计算被吃的风险
        risk += sum(self.risk_factors["be_eaten"] for offset in [-1, 0, 1]
                    if f"{num + offset}{type}" in self.discard_pile)
        # 计算被碰的风险
        risk += self.risk_factors["be_ponged"].get(self.discard_pile.count(tile), 0)
        # 计算被杠的风险
        risk += self.risk_factors["be_konged"] if self.discard_pile.count(tile) == 0 else 0
        # 计算是胡牌的风险
        risk += self.risk_factors["be_winning_tile"] if self.is_potential_win_tile(tile) else 0
        # 计算已经打出过的风险
        risk += self.risk_factors["already_discarded"] if tile in self.my_discards else 0

        # 调整风险因素权重
        self._adjust_risk_factors(risk)
        return max(risk, 0)

    def _adjust_risk_factors(self, risk):
        #根据风险值调整风险因素的权重

        factor = 1.1 if risk > 10 else 0.9 if risk < 5 else 1
        for key in self.risk_factors:
            if isinstance(self.risk_factors[key], dict):
                for sub_key in self.risk_factors[key]:
                    self.risk_factors[key][sub_key] = max(-10, min(self.risk_factors[key][sub_key] * factor, 20))
            else:
                self.risk_factors[key] = max(-10, min(self.risk_factors[key] * factor, 20))
        # 保存更新后的权重到文件
        self._save_weights()

    def is_potential_win_tile(self, tile):
        #判断一张牌是否是潜在的胡牌

        num, type = int(tile[:-1]), tile[-1]
        return self.discard_pile.count(tile) >= 2 or any(
            f"{num + offset}{type}" in self.discard_pile for offset in [-2, -1, 1, 2])

    def choose_tile_to_discard(self):
        """
        选择要打出的牌，选择价值减去风险最小的牌
        """
        scores = [(tile, self.evaluate_tile_value(tile) - self.evaluate_tile_risk(tile)) for tile in self.my_hand]
        return min(scores, key=lambda x: x[1])[0]

    def play(self, discard_pile, my_discards, my_hand, new_tile):
        """
        进行一次出牌操作
        :param discard_pile: 公共弃牌堆
        :param my_discards: 自己的弃牌列表
        :param my_hand: 自己手中的牌
        :param new_tile: 新摸到的牌
        :return: 要打出的牌
        """
        self.update_state(discard_pile, my_discards, my_hand, new_tile)
        tile_to_discard = self.choose_tile_to_discard()
        self.my_hand.remove(tile_to_discard)
        self.my_discards.append(tile_to_discard)
        self.last_discarded_tile = tile_to_discard
        return tile_to_discard

    def update_experience(self, is_winning):
        """
        根据游戏是否获胜更新权重，以积累经验
        """
        if not self.last_discarded_tile:
            return
        tile = self.last_discarded_tile
        num = int(tile[:-1])
        factor = 1.1 if is_winning else 0.9

        # 更新价值因素权重
        self._update_value_factors(tile, factor)
        # 更新牌的权重
        self._update_tile_weights(tile, num, factor)
        # 更新位置权重
        self._update_position_weights(num, factor)
        # 更新风险因素权重
        self._update_risk_factors(factor)
        # 保存更新后的权重到文件
        self._save_weights()

    def _update_value_factors(self, tile, factor):
        """
        根据游戏结果更新价值因素的权重
        :param tile: 上一次打出的牌
        :param factor: 调整因子
        """
        count = self.my_hand.count(tile) + 1
        for key, condition in [("four_of_a_kind", count >= 4), ("three_of_a_kind", count >= 3),
                               ("pair", count >= 2), ("sequence", self.is_part_of_sequence(tile))]:
            if condition:
                self.value_factors[key] = max(0.5, min(self.value_factors[key] * factor, 3.0))

    def _update_tile_weights(self, tile, num, factor):
        """
        根据游戏结果更新牌的权重
        :param tile: 上一次打出的牌
        :param num: 牌的数字
        :param factor: 调整因子
        """
        self.tile_weights[tile] = max(0.5, min(self.tile_weights[tile] * (1.2 if factor > 1 else 0.8), 2.0))
        for offset in [-1, 0, 1]:
            adjacent_num = num + offset
            if 1 <= adjacent_num <= 9:
                adjacent_tile = f"{adjacent_num}{tile[-1]}"
                if adjacent_tile in self.tile_weights:
                    self.tile_weights[adjacent_tile] = max(0.5,
                                                           min(self.tile_weights[adjacent_tile] * (
                                                               1.1 if factor > 1 else 0.9), 2.0))

    def _update_position_weights(self, num, factor):
        """
        根据游戏结果更新位置权重
        :param num: 牌的数字
        :param factor: 调整因子
        """
        self.position_weights[num] = max(-3, min(self.position_weights.get(num, 0) * factor, 3))

    def _update_risk_factors(self, factor):
        """
        根据游戏结果更新风险因素的权重
        :param factor: 调整因子
        """
        for key in self.risk_factors:
            if isinstance(self.risk_factors[key], dict):
                for sub_key in self.risk_factors[key]:
                    self.risk_factors[key][sub_key] = max(-10, min(
                        self.risk_factors[key][sub_key] * (0.9 if factor > 1 else 1.1), 20))
            else:
                self.risk_factors[key] = max(-10, min(self.risk_factors[key] * (0.9 if factor > 1 else 1.1), 20))