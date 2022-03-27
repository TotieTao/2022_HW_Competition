# %%

import numpy as np
import time
import configparser
import copy
from collections import defaultdict

# 获取数据
def get_data(filename):
    lines = open(filename, 'r').readlines()
    items = []
    for l in lines:
        tmp = l.strip()  # 删除字符串头尾空白字符
        item = [i for i in tmp.split(",")]  # 分割元素转成数组 >>[0, 4828, 774, 207, 7460, 7465, 3768, 10221, 22435]
        items.append(item)

    return items


class Site:
    def __init__(self):
        self.bandwidth = 0
        self.overload = False  # 1超载
        self.free = 0  # 剩余带宽


class User:
    def __init__(self):
        self.candidate_sites = []
        self.n = 0

    #计算候选节点的平均带宽
    def Avg(self,ssites,sites_head):

        s = [ssites[1][sites_head.index(v)] for v in self.candidate_sites]
        avg = int(sum(s)/self.n)
        return avg

    #按比例分配
    def ScaleAndSum(self,ssite,s_head):
        # print(self.candidate_sites)
        s_site = [ssite[1][s_head.index(v)] for v in self.candidate_sites]

        s_sum = sum(s_site)
        ss = [v/s_sum for v in s_site]

        return ss,s_sum



# %%
def main():
    Demand = get_data("../data/demand.csv")
    Qos = get_data("../data/qos.csv")
    Site_bandwidth = get_data("../data/site_bandwidth.csv")

    # os.makedirs("../output")
    data = open("../output/solution.txt", 'w', encoding="utf-8")

    config = configparser.ConfigParser()
    config.read("../data/config.ini")
    qos_constraint = int(config.get("config", "qos_constraint"))

    # 用户需求
    demand_head = Demand[0][1:]
    demand_value = [[int(v) for v in i[1:]] for i in Demand[1:]]

    # ssites[0] = bandwidth,ssites[1] = free, ssite[2] = overload

    ssites = np.zeros((3, len(Site_bandwidth) - 1), dtype=int)
    sites_head = []
    for i, s in enumerate(Site_bandwidth[1:]):
        sites_head.append(s[0])
        # ssites[0][i] = i
        ssites[0][i] = s[1]
        ssites[1][i] = s[1]


    # 初始化user
    users = dict()

    qos_head = Qos[0][1:]

    for u in qos_head:
        users[u] = User()

    for item in Qos[1:]:
        s = item[0]  # 节点名
        for index, u in enumerate(item[1:]):
            if int(u) < qos_constraint:  # 筛选符合user条件的节点
                users[qos_head[index]].n += 1
                users[qos_head[index]].candidate_sites.append(s)


###################################以上是数据设计###############################################


    #所有输出存储表
    output = []

    #按时间
    for demand in demand_value:
        #每行存一个user及其分配方案=> out_user[0] = 'A',out_user[1] = {'Dm':999}
        out_user = []

        users_tmp = copy.deepcopy(users)
        sites_tmp = ssites.copy() #初始化公共节点表
        for time_index, u in enumerate(users_tmp):
            user_demand = demand[demand_head.index(u)]
            if user_demand == 0:
                out_user.append([u]) #存储user名字
                continue

            #获取当前user的候选节点比例
            sites_scales, free_sum = users_tmp[u].ScaleAndSum(sites_tmp, sites_head)
            #存储user分配方案
            out = defaultdict(int)
            user_demand_1 = user_demand

            #
            if free_sum <= user_demand:
                # 若剩余带宽之和不够,则全部分配/可以优化,只分配1,跳过判题器万一查只有demand为0的user才可跳过
                for index, s in enumerate(users_tmp[u].candidate_sites):
                    s_i = sites_head.index(s)  # site索引
                    if sites_tmp[2][s_i]:  # 是否超载
                        continue

                    out[s] += sites_tmp[1][s_i]         #保存分配方案
                    user_demand_1 -= sites_tmp[1][s_i]  #在这个模块没意义,下个模块有意义
                    sites_tmp[1][s_i] = 0               #free bandwidth
                    sites_tmp[2][s_i] = 1  # 超载
            else:
                #循环知道满足demand
                while user_demand_1 != 0:
                    # print("u:{}".format(user_demand_1))
                    while user_demand_1 > 100: #小于100的不按比例分,凭直觉方便写代码/可继续优化
                        # print("user demand:{}".format(user_demand_1),end=" ")
                        sites_scales, free_sum = users_tmp[u].ScaleAndSum(sites_tmp, sites_head)
                        # print("free_sum:{}-{}".format(free_sum,sites_scales))
                        sites_scale = [int(user_demand_1 * r) for r in sites_scales]  # 根据需求获取候选节点按比例分配的带宽,因为取整四舍五入会有部分节点不满足demand,所以当demand<100时暴力分配可以把这部分补上
                        # scale_sum = sum(sites_scale)
                        # print("scale_sum:{}{}".format(scale_sum,sites_scale),end=' ')

                        # 每个节点按比例分配给user demand
                        for index, s in enumerate(users_tmp[u].candidate_sites):
                            s_i = sites_head.index(s)  # site索引
                            if sites_tmp[2][s_i]:  # 是否超载
                                continue
                            # 按候选节点顺序更新空余带宽
                            sites_tmp[1][s_i] -= sites_scale[index]  # free 减去对应分配比例的带宽
                            user_demand_1 -= sites_scale[index]  # demand更新
                            if sites_tmp[1][s_i] == 0:  # 当free恰好为0时超载，节点带宽极小时发生，可优化
                                sites_tmp[2][s_i] == 1  # 超载

                            # out.append((s,sites_scale[index]))
                            out[s] += sites_scale[index]  # 记录user_i当前site_j按比例分配的带宽

                    # 处理边缘情况，当user_demand小于100时，按比例乘得的数可能会很小，如0.01 * 100 当前节点分配1带宽，若继续按比例分配会进入循环
                    # 按节点顺序分配，如果剩余带宽不够，则全部分配
                    n = 0
                    for index, s in enumerate(users_tmp[u].candidate_sites):
                        s_i = sites_head.index(s)  # site索引
                        if sites_tmp[2][s_i]:  # 是否超载
                            n += 1
                            continue

                        # 按候选节点顺序更新空余带宽/可以加排序（待优化）/若当前节点带宽不够，则全部分配给user并记录超载
                        if sites_tmp[1][s_i] <= user_demand_1:
                            # out.append((s,sites_tmp[1][s_i]))
                            out[s] += sites_tmp[1][s_i]
                            user_demand_1 -= sites_tmp[1][s_i]
                            sites_tmp[1][s_i] = 0
                            sites_tmp[2][s_i] = 1  # 超载
                        else:
                            # out.append((s,sites_tmp[1][s_i]))
                            out[s] += user_demand_1
                            sites_tmp[1][s_i] -= user_demand_1
                            user_demand_1 = 0

                    if n == users_tmp[u].n: #若全部超载则该用户分配结束,最差结果
                        break

            out_user.append([u])
            out_user[time_index].append(out)
            # break

        output.append(out_user)
        # print(sites_tmp)
        # break
    # %%
    #输出
    for o in output:
        # print("---")
        for outuser in o:
            if len(outuser) == 1:
                print("{}:".format(outuser[0]),file=data)
            else:
                print("{}:".format(outuser[0]), end='',file=data)
                n = 1
                for k, v in outuser[1].items():
                    if n == len(outuser[1]):
                        # print("<{},{}>".format(k,v),file=data)
                        print("<{},{}>".format(k, v),file=data)
                    else:
                        # print("<{},{}>".format(k, v), end=",", file=data)
                        print("<{},{}>".format(k, v), end=",",file=data)
                        n += 1

if __name__ == "__main__":
    # start_time = time.time()
    main()
    # print("time:{}".format(time.time() - start_time))


