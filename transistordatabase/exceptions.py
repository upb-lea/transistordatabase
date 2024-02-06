"""Handling of exceptions."""
class MissingDataError(Exception):
    """Custom exception class for plecs_exporter."""

    # define the error codes & messages here
    em = {1101: "Switch conduction channel information is missing, cannot export to",
          1111: "Switch conduction channel information is missing at provided v_g, cannot export to",
          1102: "Switch turn on loss curves do not exists at every junction temperature, cannot export to",
          1103: "Switch turn off loss curves do not exists at every junction temperature, cannot export to",
          1104: "Switch turn on loss information is missing",
          1105: "Switch turn off loss information is missing",
          1201: "Diode conduction channel information is missing, cannot export to",
          1211: "Diode conduction channel information is missing at provided v_g, cannot export to",
          1202: "Diode reverse recovery loss information is missing",
          1203: "Diode reverse recovery loss curves do not exists at every junction temperature, cannot export to"}
