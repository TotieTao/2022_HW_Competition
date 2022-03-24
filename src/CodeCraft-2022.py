import numpy as np
import configparser
import copy

#获取数据
def get_data(filename):
    lines = open(filename,'r').readlines()
    items = []
    for l in lines:
        tmp = l.strip() #删除字符串头尾空白字符
        item = [i for i in tmp.split(",")] #分割元素转成数组 >>[0, 4828, 774, 207, 7460, 7465, 3768, 10221, 22435]
        items.append(item)

    return items

#候选site按free bandwidth排序/这部分设计有点冗余
def sort_freesite(Users,sites):
    users = copy.deepcopy(Users)
    for u in users:
        tmp = users[u].candidate_sites
        for s in tmp:
            tmp[s].free = sites[s].free #更新user.candidate_site表里的数据
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

#%%
def main():
    Demand = get_data("/data/demand.csv")
    Qos = get_data("/data/qos.csv")
    Site_bandwidth = get_data("/data/site_bandwidth.csv")


    data = open("/output/solution.txt", 'w', encoding="utf-8")

    config = configparser.ConfigParser()
    config.read("/data/config.ini")
    qos_constraint = int(config.get("config","qos_constraint"))

    #用户需求
    demand_head = Demand[0][1:]
    demand_value = [i[1:] for i in Demand[1:]]

    #初始化节点
    Sites = dict()
    for s in Site_bandwidth[1:]:
        site = Site()
        site.bandwidth = int(s[1])
        site.free = int(s[1])
        Sites[s[0]] = site
    sites = Sites

    #初始化user
    users = dict()

    qos_head = Qos[0][1:]

    for u in qos_head:
        users[u] = User()

    for item in Qos[1:]:
        s = item[0] #节点名
        for index,u in enumerate(item[1:]):
            if int(u) <= qos_constraint: #筛选符合user qos条件的节点
                users[qos_head[index]].n += 1
                users[qos_head[index]].candidate_sites[s] = sites[s]

    #user按site数排序
    users = sorted(users.items(),key=lambda l:l[1].n, reverse=False)
    users = {u[0]:u[1] for u in users}

    # 候选site按free bandwidth排序
    users = sort_freesite(users,sites)
    #%%
    for demand in demand_value:
        # print("---")
        users_tmp = copy.deepcopy(users)
        sites_tmp = copy.deepcopy(Sites)
        for u in users_tmp:
            user_demand = int(demand[demand_head.index(u)])
            if user_demand == 0:
                print("%s:"%(u),file=data)
                continue
            out = dict()
            for s in users_tmp[u].candidate_sites:
                if sites_tmp[s].overload:
                    continue
                if sites_tmp[s].free > user_demand: #空闲带宽多则直接分配,并服务下个用户
                    out[s] = user_demand
                    sites_tmp[s].free = sites_tmp[s].free - user_demand
                    break
                else: #否则超载了接着找下个节点
                    out[s] = sites_tmp[s].free
                    user_demand = user_demand - sites_tmp[s].free
                    sites_tmp[s].overload = 1
            print("%s:"%u,end="",file=data)
            # print("%s:"%u,end="")
            n = 1
            for k,v in out.items():
                if n == len(out):
                    print("<{},{}>".format(k,v),file=data)
                    # print("<{},{}>".format(k,v))
                else:
                    print("<{},{}>".format(k, v), end=",", file=data)
                    # print("<{},{}>".format(k, v), end=",")
                    n += 1
            #服务完一个user后更新sites空余带宽并升序
            users_tmp = sort_freesite(users_tmp,sites_tmp)



if __name__ == "__main__":
    main()