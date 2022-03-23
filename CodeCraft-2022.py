import numpy as np
import sys
import os

#获取数据
def get_data(filename):
    lines = open(filename,'r').readlines()
    items = []
    for l in lines:
        tmp = l.strip() #删除字符串头尾空白字符
        item = [i for i in tmp.split(",")] #分割元素转成数组 >>[0, 4828, 774, 207, 7460, 7465, 3768, 10221, 22435]
        items.append(item)

    return items

#候选site按free bandwidth排序
def update_freesite(users,sites):
    for u in users:
        tmp = users[u].candidate_sites
        for s in tmp:
            tmp[s].free = sites[s].free #更新candidate表里的数据
        tmp = sorted(tmp.items(),key=lambda l:l[1].free, reverse=False)
        users[u].candidate_sites = {u[0]:u[1] for u in tmp}
    return users

class Site:
    def __init__(self):
        self.bandwidth = 0
        self.overload = False #1超载
        self.free = 0 #剩余带宽

class User:
    def __init__(self):
        self.candidate_sites = dict()
        self.n = 0

def main():
    Demand = get_data("./demand.csv")
    Qos = get_data("./qos.csv")
    Site_bandwidth = get_data("./site_bandwidth.csv")

    os.makedirs("../output")
    data = open("../output/solution.txt", 'w', encoding="utf-8")


    #用户需求
    demand_h = Demand[0][1:]
    demand_v = [i[1:] for i in Demand[1:]]
    #初始化节点
    Sites = dict()
    for s in Site_bandwidth[1:]:
        site = Site()
        site.bandwidth = int(s[1])
        site.free = int(s[1])
        Sites[s[0]] = site

    sites = Sites

    users = dict()
    qos_h = Qos[0][1:]

    for u in qos_h:
        users[u] = User()

    for item in Qos[1:]:
        s = item[0] #节点名
        for index,u in enumerate(item[1:]):
            if int(u) < 400: #筛选符合user条件的节点
                users[qos_h[index]].n += 1
                users[qos_h[index]].candidate_sites[s] = sites[s]

    #user按site数排序
    users = sorted(users.items(),key=lambda l:l[1].n, reverse=False)
    users = {u[0]:u[1] for u in users}

    # 候选site按free bandwidth排序
    users = update_freesite(users,sites)

    for demand in demand_v:
        # print("---")
        users_tmp = users
        sites = Sites
        for u in users_tmp:
            user_demand = int(demand[demand_h.index(u)])
            if user_demand == 0:
                print(u)
                continue
            out = dict()
            for s in users_tmp[u].candidate_sites:

                if sites[s].overload:
                    continue
                if sites[s].free > user_demand: #空闲带宽多则直接分配,并服务下个用户
                    out[s] = user_demand
                    sites[s].free = sites[s].free - user_demand
                    break
                else: #否则接着找下个节点
                    out[s] = sites[s].free
                    user_demand = user_demand - sites[s].free
                    sites[s].overload = 1
            print("%s:"%u,end="",file=data)
            for k,v in out.items():
                print("<{},{}>".format(k,v),end=" ",file=data)
            print('', file=data)
            #服务完一个user后更新sites空余带宽并升序
            users_tmp = update_freesite(users_tmp,sites)



if __name__ == "__main__":
    main()
