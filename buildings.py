class Building:
    def __init__(self, obj):
        self.team = obj["team"]

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

class Barracks(Building):
    def __init__(self, obj):
        super().__init__(obj)

    @staticmethod
    def buildcost():
        return((50,0))

    @staticmethod
    def housing():
        return 0

class Range(Building):
    def __init__(self, obj):
        super().__init__(obj)

    @staticmethod
    def buildcost():
        return((70,0))

    @staticmethod
    def housing():
        return 0

class Stable(Building):
    def __init__(self, obj):
        super().__init__(obj)

    @staticmethod
    def buildcost():
        return((90,0))

    @staticmethod
    def housing():
        return 0

class House(Building):
    def __init__(self, obj):
        super().__init__(obj)

    @staticmethod
    def buildcost():
        return((90,40))

    @staticmethod
    def housing():
        return 9
