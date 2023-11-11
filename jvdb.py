from motor import motor_asyncio

class MongoDB:
    def __init__(self, url: str):
        self.client = motor_asyncio.AsyncIOMotorClient(url)
        self.db = self.client.giveawaybot
        self.mygiveaways = self.db.mygiveaways
    
    async def get_giveawayid(self, userid: int):
        user = await self.mygiveaways.find_one({"_id": userid})
        if user != None:
            userDb = self.db[str(userid)]
            return userDb
        else:
            return None
    
    async def add_giveawayid(self, userid: int):
        if not (await self.mygiveaways.find_one({"_id": userid})):
            await self.mygiveaways.insert_one({"_id": userid})
            userDb = self.db[str(userid)]
            return userDb
        else:
            return None
    
    async def delete_giveawayid(self, userid: int):
        user = await self.mygiveaways.find_one({"_id": userid})
        if user != None:
            await self.mygiveaways.delete_one(user)
            userDb = self.db[str(userid)]
            await userDb.drop()
            return True
        else:
            return None
    
    async def get_giveaway_users(self, userid: int):
        userDb = await self.get_giveawayid(userid)
        if userDb != None:
            giveaway = userDb.find({})
            if giveaway != None:
                count = await userDb.count_documents({})
                return await giveaway.to_list(count)
            else:
                return None
        else:
            return None
    
    async def add_giveaway(self, userid: int, winners: int, msg_text: str, giveaway_text: str):
        userDb = await self.add_giveawayid(userid)
        if userDb != None:
            await userDb.insert_one({"_id": "data", "winners": winners, "msg_text": msg_text, "giveaway_text": giveaway_text})
            return True
        else:
            return None
    
    async def get_giveaway_users_count(self, userid: int):
        userDb = await self.get_giveawayid(userid)
        if userDb != None:
            if giveaway := await userDb.count_documents({}):
                return giveaway
            else:
                return None
        else:
            return None
    
    async def add_giveaway_user(self, giveawayId: int, userId: int):
        userDb = await self.get_giveawayid(giveawayId)
        if userDb != None:
            if (await userDb.find_one({"_id": userId})):
                return None
            await userDb.insert_one({"_id": userId})
            return userDb