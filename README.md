# Raw data

In raw/ there are a few files:

-   `timezone.csv`: a table mapping US state to their timezone
    (expresses in degrees, 360/24=15 degrees equals to one hour, so
    e.g. -60 is UTC-4) in winter and summer, and some notes on
    exceptions; hand made from Wikipedia.
-   `dst.csv`: dates of introduction and removal of DST; list obtained
    from Rodolfo, just added 1974.
-   `geolocation.psv`: a list of US "features", used to map counties
    to latitude and longitude; obtained from
    https://www.usgs.gov/core-science-systems/ngp/board-on-geographic-names/download-gnis-data;
    this file is zipped to stay below the limit in size, unzip before
    proceeding.
-   `counties_timezone_exceptions.csv`: exceptions to state-wide
    timezones, hand made from
    https://github.com/geanders/countytimezones/blob/master/data-raw/clean_timezones_data.R.
-   `aXXXX.csv`: accidents files.


# process.py

The process script normalizes the data of accidents, and adds more
features, then it "caches" the final results in `_data.csv`;
intermediate results are also cached in `derived/_*.csv`. If process
is called and some intermediate data is cached, the script will reuse
it.

The derived data is:

-   `derived/_states.csv`: a table of state numerical id and
    two-letter identifier;
-   `derived/_counties.csv`: a table with state and county identifiers
    (numerical and alphabetical), and their approximated latitude and
    longitude (computed as the average from all the features in that
    county);
-   `derived/_accidents.csv`: a table of all accidents, including
    state identifier, time as year/month/day/hour/minute, case
    identifier and latitude and longitude (if present in the accident
    data, those coordinates are used, otherwise they are inferred from
    the county);
-   `_data.csv`: a table of all accidents with much more data:
    -   state identifier (numerical and alphabetical);
    -   time as a string (so that we can parse it to a Python
        datetime);
    -   time in components: year/month/day/hour/minute;
    -   `ST_CASE`: case identifier;
    -   `LAT`, `LNG`: coordinates of the accident;
    -   `TZ_NO_DST`, `TZ_DST`: timezone in degrees when DST is not in
        effect and when it is;
    -   `DAYS_FROM_DST_SWITCH`: number of days from the last switch
        to/from DST (intended to filter out days right after the
        switch since they might be outlier);
    -   `DST_DELTA`, that is whether the last switch was to DST (1) or
        from DST (-1);
    -   `DST`: a literal yes if the accident happened during DST or a
        literal no;
    -   `OFFSET_LNG`: distance in degrees from the accident to the
        center of the timezone (accounting for DST or no DST); this
        can be used to compare accidents at similar "relative times to
        timezone" across different timezones;
    -   `OFFSET_MINUTES`: same information as `OFFSET_LNG`, but
        expressed in minutes, and quantized; the quantization is done
        in such a way to have similar number of accidents in the two
        central buckets, (-70', -10') (expressed as the center, -40'),
        and (-10', 50') (expressed as 20');
    -   `DAY_MINUTE`: minute of the day when the accident happened.

The accident data is cleaned up a bit:

-   some states are excluded since their timezone behaves weirdly, or
    have too many exceptions;
-   remove accidents with hour=24 or hour=minute=99, which probably
    mean the time of day was not recorded;
-   further remove accidents whose time cannot be parsed in Python;
-   remove accidents with bad location, outside of US.


# plot.py

This script executes process then reads `_data,csv`, proceed to
process the table further, and plots some graphs.

The data is processed by:

-   adding `HOUR`: the hour of the accidents expressed form 5 to 29,
    to be able to plot graphs starting at 5AM (which is the global
    minimum almost across all slices of the data;
-   accidents during the first week after the DST switch are removed;
-   removing small slices: if the set of accidents happening in a
    specific offset quant (with or without DST) has less than 10k
    accidents, it is removed from the table.

The plots are:

-   `01_dst_nodst_comparison`: total number of accidents by hour of
    day, grouped by whether they happened during DST or not; the idea
    was to see whether the patterns during winter or summer were
    different due to different duration of daylight;
-   `02_nodst_by_offset`: plot of accidents happening not during DST,
    by hour of day, grouped by offset quant; if the hypothesis is
    correct, we should see one line anticipate the other by one hour;
-   `03_dst_by_offset`: same but for accidents during DST;


# ks_stats.py

Similarly to `plot.py`, this executes process, when does some further
processing, and finally prints and plots some statistics.

The processing is comprised of:
-   remove first week after DST switch, and small slices as `plot.py`;
-   split the data in accidents happening during DST or not; each is
    treated independently.

The following happens for accidents in DST and not in DST, processed
separately and independently.

The script computes, in `_get_probs`, for each quant, a list of 24 values, the
probability that an accident in that quant happened at that hour of
the day.

It then prints the total number of the accidents happening at that
quant (to make sure the volume of the two central buckets is similar).

The main process though is computing p-values for these statistical
test: if we take the data of quant x and quant y, and we shift the
accident time of the data of quant y by m minutes, does it look like
they come from the same distribution?

This is tested for all pairs of quants, and delays between -60' and
60' at steps of 15', and all the resulting data is printed and plotted
as `04_js_test_values_dst|nodst`.

If the hypothesis is correct, we should see a lower p-value for the
delay corresponding to the difference between the quant times.


# Conclusions and further work

The hourly plots by offset quant show intuitively some peaks occurring
at different times, but the statistical test don't show evidence of
the full distribution being shifted. We might have better luck trying
to isolate each peak and analyze it separately.

One way to do this is to fit a sum of unimodal distributions to the
data, trying to use them to model the peaks, and then look at mean and
standard deviation of corresponding peaks and see if they are
statistical significant. The problem with that is that we need a
circular distribution, a simple Gaussian fit would not work, and this
is complicated to do with standard packages.

Another change to the analysis would be to normalize the accident data
to the road usage, as for sure the number of accidents is related to
that, and there might be shifts in usage patterns by time and/or
location that can muddle the signal we're looking for.
