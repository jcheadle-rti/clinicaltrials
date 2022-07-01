# Clean CT.gov input data
library(tidyverse)
library(readr)
library(magrittr)
library(janitor)
library(stringr)
library(reshape2)

# Load Data
input_path <- "C:/Users/jcheadle/projects/clinicaltrials/inputs"
output_path <- input_path
filename <- "heal_clintrials_inputs.csv"

raw_data <- read_csv(paste0(input_path, "/", filename))
colnames(raw_data) <- janitor::make_clean_names(colnames(raw_data),"snake")
raw_data %<>% rename(nctid = clinical_trial_gov_nct_source_lists)

# Separate rows appropriately
sep_data <- raw_data %>% separate_rows(nctid, sep = "\\),")

# extract NCT ID, drop NAs
sep_data %<>% mutate(
  nctid = str_trim(nctid),
  clean_nctid = str_extract(nctid, "^NCT[0-9]*")
) %>% select(-nctid) %>% rename(nctid = clean_nctid) %>%
  drop_na(nctid)

write_csv(sep_data,
          file = paste0(input_path,"/","heal_clintrials_cleaned.csv"))
