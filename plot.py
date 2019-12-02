import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

import utils
from process import main as process_main


def _format_ax(ax):
  ax.set_xticks(range(5, 29), minor=True)
  ax.set_xticks(range(6, 30, 3), minor=False)
  ax.set_xticklabels(range(6, 24, 3) + range(0, 5, 3))
  ax.set_ylim(0.01, 0.07)
  ax.grid(which='major', alpha=0.8, linestyle='-')
  ax.grid(which='minor', alpha=0.5, linestyle='-')

  vals = ax.get_yticks()
  ax.set_yticklabels(['{:,.2%}'.format(x) for x in vals])

  return ax


def plot_dst_nodst_comparison(data):
  fig, ax = plt.subplots(figsize=(16, 9))
  _ = data.groupby(["DST", "HOUR"])["STATE"].count()\
          .groupby(["DST"]).transform(lambda x : x / x.sum())\
          .reset_index().rename(columns={"STATE": "ACCIDENTS"})
  sns.lineplot(data=_, x="HOUR", y="ACCIDENTS", hue="DST", ax=ax)
  _format_ax(ax)
  plt.savefig("plots/01_dst_nodst_comparison.png")


def plot_by_offset(data):
  fig, ax = plt.subplots(figsize=(16, 9))
  _ = data.groupby(["DST", "OFFSET_MINUTES", "HOUR"])["STATE"].count()\
          .groupby(["DST", "OFFSET_MINUTES"]).transform(lambda x : x / x.sum())\
          .reset_index().rename(columns={"STATE": "ACCIDENTS"})
  _ = _[_["DST"] == "no"]
  sns.lineplot(data=_, x="HOUR", y="ACCIDENTS", hue="OFFSET_MINUTES", ax=ax)
  _format_ax(ax)
  plt.savefig("plots/02_nodst_by_offset.png")

  fig, ax = plt.subplots(figsize=(16, 9))
  _ = data.groupby(["DST", "OFFSET_MINUTES", "HOUR"])["STATE"].count()\
          .groupby(["DST", "OFFSET_MINUTES"]).transform(lambda x : x / x.sum())\
          .reset_index().rename(columns={"STATE": "ACCIDENTS"})
  _ = _[_["DST"] == "yes"]
  sns.lineplot(data=_, x="HOUR", y="ACCIDENTS", hue="OFFSET_MINUTES", ax=ax)
  _format_ax(ax)
  plt.savefig("plots/03_dst_by_offset.png")


def main():
  sns.set_style("whitegrid")

  data = process_main()
  data["HOUR"] = np.where(data["HOUR"] <= 4, data["HOUR"] + 24, data["HOUR"])
  data = utils.remove_first_week_after_dst_switch(data)

  plot_dst_nodst_comparison(data)

  data = utils.remove_small_groups(data, ["DST", "OFFSET_MINUTES"])
  plot_by_offset(data)


if __name__ == "__main__":
  main()
