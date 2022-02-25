## Visualization script for climate scenarios
library(tidyverse)
library(ggpubr)

# ####################SUPPLY-DEMAND METRICS
folder <- dirname(rstudioapi::getSourceEditorContext()$path)

# data <- read.csv(file.path(folder, '..', 'results', 'final_GHA.csv'))

data <- read.csv(file.path(folder, 'figures', 'test_data.csv'))

data$year = factor(data$year, 
                       levels=c("2030","2050","2080"),
                       labels=c("2030","2050","2080")
                   )

data$returnperiod = factor(data$returnperiod, 
                   # levels=c("rp00100","rp00250",
                   #          "rp00500","rp01000"),
                   levels=c("100-year","250-year",
                            "500-year","1000-year"),
                   labels=c("100-year","250-year",
                            "500-year","1000-year")
)
# unique(data$climatescenario)
data$climatescenario = factor(data$climatescenario, 
                   levels=c("rcp4p5","rcp8p5"),
                   labels=c("RCP 4.5, SSP 2", "RCP 8.5, SSP 3")
)

data$cost = (data$cost/1e6)

ggplot(data, aes(x=year, y=cost, group=climatescenario)) +
  geom_line(aes(linetype=climatescenario, color=climatescenario))+
  geom_point(aes(shape=climatescenario, color=climatescenario))+
  scale_color_manual(values=c("#0072B2", "#D55E00")) +  
  theme( legend.position = "bottom", 
         # axis.text.x = element_text(angle = 0, hjust = 0)
         ) + 
  labs(colour=NULL,
       title = "Mobile Infrastructure Damage by Forecast Year, Climate Scenario and Flood Return Period",
       subtitle = "Riverine Model: MIROC-ESM-CHEM. Coastal Model: RISES-AM",
       x = NULL, y = "Damage Cost to Mobile Infrastructure ($Mn)") + 
  theme(panel.spacing = unit(0.6, "lines")) + expand_limits(y=0) +
  guides(linetype=guide_legend(ncol=2, title='Scenario'),
         shape=guide_legend(ncol=2, title='Scenario'),
         color=guide_legend(ncol=2, title='Scenario')) + 
  scale_x_discrete(expand = c(0, 0.15)) +  
  scale_y_continuous(expand = c(0, 0), limits=c(0,300)) +  
  facet_wrap(vars(returnperiod), scales = "free")

path = file.path(folder, 'figures', 'GHA', 'GHA_economic_cost.png')
ggsave(path, units="in", width=8, height=6, dpi=300)
