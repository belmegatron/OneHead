


class DataBaseTest(TestCase):

    def setUp(self):
        self.scoreboard = [{"name": "RBEEZAY", "win": 10, "loss": 0, "ratio": 10},
                           {"name": "GPP", "win": 10, "loss": 0, "ratio": 10},
                           {"name": "LOZZA", "win": 10, "loss": 0, "ratio": 10},
                           {"name": "JEFFERIES", "win": 10, "loss": 0, "ratio": 10},
                           {"name": "JAMES", "win": 10, "loss": 0, "ratio": 10},
                           {"name": "PECRO", "win": 0, "loss": 10, "ratio": 0}]

    def test_calculate_positions_tie(self):
        foo = Database._calculate_positions(self.scoreboard, "ratio")

