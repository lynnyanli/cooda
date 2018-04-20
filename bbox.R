library(ggplot2)
library(reshape2)
library(RColorBrewer)
display.brewer.all()

data1<-read.csv("D:\\我的坚果云\\修改\\PV-IA\\图\\6region.csv",header=T)
y<-c(1:25)
data2<-data.frame(y,data1)
data3<-melt(data2,id.vars="y")

bbox<-ggplot(data3,aes(x=variable,y=value),color=variable)+geom_boxplot(aes(fill=factor(variable)))+
      guides(fill=FALSE)+
      scale_fill_brewer(palette="Pastel2")+
      ylab("Gross annual revenue (RMB/kW)")+xlab("Region")+
#coord_flip()+
      theme(legend.position="none")+theme_minimal()+scale_y_continuous(limits=c(0,1100))
bbox