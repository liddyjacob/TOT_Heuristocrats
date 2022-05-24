class Building:
    def __init__(self, obj):
        self.team = obj["team"]
        self.x = obj['x']
        self.y = obj['y']
        self.move_stack = []
        self.id = obj['id']
        self.hp = obj['hp']
        print(obj)

    # for updating health and stuff
    def update(self, obj):
        pass

class Townhall(Building):
    def __init__(self, obj):
        super().__init__(obj)

    @staticmethod
    def buildcost():
        return((200,0))

    @staticmethod
    def housing():
        return 4

    @staticmethod
    def max_health():
        return 80

    @staticmethod
    def rep():
        return 'w'

class Barracks(Building):
    def __init__(self, obj):
        super().__init__(obj)

    @staticmethod
    def buildcost():
        return((50,0))

    @staticmethod
    def housing():
        return 0

    @staticmethod
    def max_health():
        return 60

    @staticmethod
    def rep():
        return 'b'

class Range(Building):
    def __init__(self, obj):
        super().__init__(obj)

    @staticmethod
    def buildcost():
        return((70,0))

    @staticmethod
    def housing():
        return 0

    @staticmethod
    def max_health():
        return 60

    @staticmethod
    def rep():
        return 'r'


class Stable(Building):
    def __init__(self, obj):
        super().__init__(obj)

    @staticmethod
    def buildcost():
        return((90,0))

    @staticmethod
    def housing():
        return 0

    @staticmethod
    def max_health():
        return 60

    @staticmethod
    def rep():
        return 's'

class House(Building):
    def __init__(self, obj):
        super().__init__(obj)

    @staticmethod
    def buildcost():
        return((90,40))

    @staticmethod
    def housing():
        return 9

    @staticmethod
    def max_health():
        return 40

    @staticmethod
    def rep():
        return 'h'