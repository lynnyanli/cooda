#!/usr/bin/python
# -*- coding: UTF-8 -*-

import numpy as np
import random
import networkx as nx
import pandas as pd
import sys
import itertools
import copy

#action 1 or 0, join or not

class CFer(object):
    def __init__(self,information_scale,amount,low_threshold,high_threshold,graph_type='BA',degree=10):
        self.amount=amount
        self.all_agent=[]

        self.budge_threshold=[low_threshold]*self.amount
        self.persuaded_threshold=[high_threshold]*self.amount

        self.G=nx.Graph()
        self.graph_type=graph_type
        self.degree=degree

        self.initial_join=0.5
        self.action=[0]*self.amount
        self.valuation=[]

        self.public_experience_project=0
        self.public_experience_default=0

        self.agent_join_project=[[] for i in range(self.amount)]

        # 0 for private, 1 for friends, 2 for public
        self.information_scale=information_scale

        #cost 6000RMB/KW
        self.unitcost=6000

        self.total_join=[]

    def populate(self):
        self.all_agent=list(range(self.amount))
        random.shuffle(self.all_agent)
        for i in self.all_agent[0:int(self.amount*self.initial_join)]:
            self.action[i]=1
            self.agent_join_project[i].append(-1)
        self.public_experience_project+=1

        if self.graph_type == 'BA':
            self.G=nx.random_graphs.barabasi_albert_graph(self.amount,self.degree)
        elif self.graph_type == 'RG':
            self.G = nx.random_graphs.random_regular_graph(self.degree,self.amount)
        elif self.graph_type == 'ER':
            self.G = nx.random_graphs.erdos_renyi_graph(self.amount,self.degree)
        elif self.graph_type == 'WS':
            self.G = nx.random_graphs.watts_strogatz_graph(self.amount,self.degree,0.3)

        inter_valuation=np.random.random(self.amount)/100*10
        self.valuation=[self.unitcost*(1+i)**20 for i in inter_valuation]

    def is_affected(self,node):
        count_action=0
        count_no_action=0
        for neighbor in self.G.neighbors(node):
                if self.action[neighbor]:
                    count_action+=1
                else:
                    count_no_action+=1

        if (count_action+count_no_action) == 0:
            print("%d"%self.G.degree(node))
            return -1
        else:
            return float(count_action)/(count_action+count_no_action)

    def default_ratio(self,node,proj_statues):
        if self.information_scale==0:
            return self.know_default(node,proj_statues)
        elif self.information_scale==1:
            max_default=self.know_default(node,proj_statues)
            for neighbor in self.G.neighbors(node):
                x=self.know_default(neighbor,proj_statues)
                if max_default<x:
                        max_default=x
            return max_default
        elif self.information_scale==2:
            return self.public_experience_default/self.public_experience_project

    def forecast(self,node,shareratio,projectrevenue,proj_statues):
        defaultratio=self.default_ratio(node,proj_statues)
        revenue=projectrevenue*(defaultratio*0.5+(1-defaultratio))*shareratio*20
        if revenue>self.valuation[node]:
            return True
        else:
            return False

    def update(self,proj_statues,whichproject,shareratio,projectrevenue,projectscale):
        new_action=[0]*self.amount
        count_join=0
        count_isolate_node=0
        random.shuffle(self.all_agent)
        for node in self.all_agent:
            affectratio=self.is_affected(node)
            if affectratio == -1:
                count_isolate_node+=1
            else:
                if affectratio<=self.budge_threshold[node]:
                    continue
                elif affectratio<=self.persuaded_threshold[node]:
                    if self.forecast(node,shareratio,projectrevenue,proj_statues):
                        new_action[node]=1
                        count_join+=1
                        self.agent_join_project[node].append(whichproject)
                elif affectratio>self.persuaded_threshold[node]:
                    new_action[node]=1
                    count_join+=1
                    self.agent_join_project[node].append(whichproject)
            if count_join>=projectscale:
                break
        self.action=new_action
        if count_isolate_node:
            print('There are %d isolate nodes, %d join' %(count_isolate_node,count_join))
        self.total_join.append(count_join)
        return count_join

    def know_default(self,node,proj_statues):
        count_project=len(self.agent_join_project[node])
        if count_project==0:
            return 0
        count_default=0
        for proj in self.agent_join_project[node]:
            if proj_statues[proj]==0:
                count_default+=1
        return count_default/count_project

class platform (object):
    def __init__(self,projects_amount,how_long_projectperiod,weather_status):
        self.projects_amount=projects_amount
        self.how_long_projectperiod=how_long_projectperiod
        self.proj_scale=[]

        self.proj_statues=[1]*self.projects_amount
        self.proj_company_invest_ratio=[]
        self.weather_status=weather_status
        self.solar_ratio=[]
        self.fit=0.65
        #cost 6000RMB/KW
        self.unitcost=6000
        self.history_ave_annual_hours=1234.533891

    def gen_projects(self,cfer_amount):
        solar_data=pd.read_csv('data.csv')
        if self.weather_status==0:
            self.solar_ratio=solar_data['LOW']
        else:
            self.solar_ratio=solar_data['HIGH']
        self.proj_scale=np.random.random_integers(int(cfer_amount/10),cfer_amount,self.projects_amount)

    def if_default(self,whichproject,shareratio,penalty):
        discount=0.06
        dr=sum([(1/(1+discount))**i for i in range(20)])
        obey_revenue=(self.history_ave_annual_hours*self.fit*(1-shareratio)*dr)*(1-self.proj_company_invest_ratio[whichproject])*self.proj_scale[whichproject]+(self.history_ave_annual_hours*self.fit*dr-self.unitcost)*self.proj_company_invest_ratio[whichproject]*self.proj_scale[whichproject]
        default_revenue=-penalty*self.proj_scale[whichproject]+(self.history_ave_annual_hours*0.5*self.fit*(1-shareratio)*dr+self.unitcost*0.5)*(1-self.proj_company_invest_ratio[whichproject])*self.proj_scale[whichproject]+(self.history_ave_annual_hours*self.fit*dr-self.unitcost)*0.5*self.proj_company_invest_ratio[whichproject]*self.proj_scale[whichproject]
        if default_revenue-obey_revenue-penalty>0:
            return True
        else:
            return False

class crowdfunding(object):
    def __init__(self,how_many_cfers,shareratio,penalty,low,high,weather_status=1,information_scale=0):
        self.how_many_cfers=how_many_cfers
        self.how_many_projects=24
        self.how_long_projectperiod=24
        self.shareratio=shareratio
        #penalty if for each kW PV
        self.penalty=penalty
        self.weather_status=weather_status
        self.information_scale=information_scale
        self.low_threshold=low
        self.high_threshold=high

    def runonce(self):
        people=CFer(self.information_scale,self.how_many_cfers,self.low_threshold,self.high_threshold)
        people.populate()
        plat=platform(self.how_many_projects,self.how_long_projectperiod,self.weather_status)
        plat.gen_projects(self.how_many_cfers)
        count_default=0
        record_default=[]
        join_scale=[]

        for t in range(self.how_long_projectperiod):
            if t< self.how_many_projects:
                lastyear_revenue=[plat.solar_ratio[t+i] for i in range(12)]
                project_revenue=sum(lastyear_revenue)*plat.fit
                join_scale.append(people.update(plat.proj_statues,t,self.shareratio,project_revenue,plat.proj_scale[t]))
                plat.proj_company_invest_ratio.append(1-join_scale[t]/plat.proj_scale[t])
                if join_scale[t]>0:
                    people.public_experience_project+=1
                    if plat.if_default(t,self.shareratio,self.penalty):
                        count_default+=1
                        plat.proj_statues[t]=0
                        people.public_experience_default+=1
                        record_default.append(t)

        return count_default/people.public_experience_project,1-sum(plat.proj_company_invest_ratio)/self.how_many_projects


def run(times,shareratio,penalty,low,high,information_scale):
    default=[]
    join=[]
    for i in range(times):
        IA_PV=crowdfunding(1000,shareratio,penalty,low,high,1,information_scale)
        default_ratio,join_ratio=IA_PV.runonce()
        default.append(default_ratio)
        join.append(join_ratio)
    return default,join

sensetiveanalyse={'shareratio':[i*0.05+0.75 for i in range(6)],'high':[i*0.05+0.75 for i in range(6)],'low':[i*0.05 for i in range(6)],\
 	'penalty':[i*500 for i in range(6)],'inform':[0,1,2]}
simulationo=['shareratio','penalty','low','high','inform']

for i in range(len(simulationo)):
   simulationobject=sensetiveanalyse[simulationo[i]] 
   filename_join="join_%s.csv"%(simulationo[i])
   filename_default="default_%s.csv"%(simulationo[i])
   skrr=3000*i
   with open(filename_join,"w") as f_j:
       with open(filename_default,"w") as f_d:
           for j in range(len(simulationobject)):
               para=[500,0.9,0,0.2,0.8,0]
               para[i+1]=simulationobject[j]
               default,join=run(para[0],para[1],para[2],para[3],para[4],para[5])
               f_d.write("%f"%simulationobject[j])
               f_j.write("%f"%simulationobject[j])
               for m in range(len(default)):
                   f_j.write(",%f"%join[m])
                   f_d.write(",%f"%default[m])
                   skrr+=1
                   strr = '(●\'-\'●)ﾉ'+'-'*(skrr//270)+'Ｏ xiu~'
                   if skrr==13499:
                       strr+='\n'+'Paaa！'+'\n'
                   elif skrr==7299:
                       print('\n就快啦~')
                   elif skrr==10999:
                       print('\n马上马上~')
                   sys.stdout.write('\r'+'[%s%%]'%(skrr//135+1)+strr)
                   sys.stdout.flush()
               f_d.write("\n")
               f_j.write("\n")
#
#dual policy
#'penalty':[i*500 for i in range(6)],'inform':[0,1,2]
#dualsimulation=['penalty','inform']
#dpenalty=[i*300 for i in range(11)]
#dinform=[0,1,2]
#filename_djoin="dual_join.csv"
#filename_ddefault="dual_default.csv"
#with open(filename_djoin,"w") as f_dj:
#    with open(filename_ddefault,"w") as f_dd:
#        for i in range(len(dpenalty)):
#            for j in range(len(dinform)):
#                default,join=run(500,0.9,dpenalty[i],0.2,0.8,dinform[j])
#                avgd=sum(default)/len(default)
#                avgj=sum(join)/len(join)
#                f_dd.write(",%f"%avgd)
#                f_dj.write(",%f"%avgj)
#            f_dj.write("\n")
#            f_dd.write("\n")

