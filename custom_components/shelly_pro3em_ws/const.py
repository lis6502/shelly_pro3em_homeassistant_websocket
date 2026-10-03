"""Constants for shelly_pro3em_ws."""

DOMAIN = "shelly_pro3em_ws"
CONF_HOST = "host"

# Device sends partial NotifyStatus; these keys live under params["em:0"].
EM_KEYS = (
    "a_act_power",
    "a_aprt_power",
    "a_current",
    "a_freq",
    "a_pf",
    "a_voltage",
    "b_act_power",
    "b_aprt_power",
    "b_current",
    "b_freq",
    "b_pf",
    "b_voltage",
    "c_act_power",
    "c_aprt_power",
    "c_current",
    "c_freq",
    "c_pf",
    "c_voltage",
    "n_current",
    "total_act_power",
    "total_aprt_power",
    "total_current",
)

# Energy counters (Wh), pushed every ~60 s under params["emdata:0"].
EMDATA_KEYS = (
    "a_total_act_energy",
    "a_total_act_ret_energy",
    "b_total_act_energy",
    "b_total_act_ret_energy",
    "c_total_act_energy",
    "c_total_act_ret_energy",
    "total_act",
    "total_act_ret",
)
