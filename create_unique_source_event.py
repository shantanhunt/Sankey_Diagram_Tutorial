import seaborn as sns
import pandas as pd

# Working on the nodes_dict
data = pd.read_csv('formatted_raw_to_ripe.csv')[
    ['user_id', 'event_name', 'time_event', 'event_type', 'rank_event', 'next_event', 'time_to_next']] # may neeed to remove index

all_events = list(data.event_name.unique())

# Create a set of colors that you'd like to use in your plot.
palette = ['50BE97', 'E4655C', 'FCC865',
           'BFD6DE', '3E5066', '353A3E', 'E6E6E6']
#  Here, I passed the colors as HEX, but we need to pass it as RGB. This loop will convert from HEX to RGB:
for i, col in enumerate(palette):
    palette[i] = tuple(int(col[i:i + 2], 16) for i in (0, 2, 4))

# Append a Seaborn complementary palette to your palette in case you did not provide enough colors to style every event
complementary_palette = sns.color_palette(
    "deep", len(all_events) - len(palette))
if len(complementary_palette) > 0:
    palette.extend(complementary_palette)

output = dict()
output.update({'nodes_dict': dict()})

i = 0
for rank_event in data.rank_event.unique():  # For each rank of event...
    # Create a new key equal to the rank...
    output['nodes_dict'].update(
        {rank_event: dict()}
    )

    # Look at all the events that were done at this step of the funnel...
    all_events_at_this_rank = data[data.rank_event ==
                                   rank_event].event_name.unique()

    # Read the colors for these events and store them in a list...
    rank_palette = []
    for event in all_events_at_this_rank:
        rank_palette.append(palette[list(all_events).index(event)])

    # Keep trace of the events' names, colors and indices.
    output['nodes_dict'][rank_event].update(
        {
            'sources': list(all_events_at_this_rank),
            'color': rank_palette,
            'sources_index': list(range(i, i + len(all_events_at_this_rank)))
        }
    )
    # Finally, increment by the length of this rank's available events to make sure next indices will not be chosen from existing ones
    i += len(output['nodes_dict'][rank_event]['sources_index'])

    ############################# Next Script ##########################
    # Working on the links_dict

    output.update({'links_dict': dict()})

    # Group the DataFrame by user_id and rank_event
    grouped = data.groupby(['user_id', 'rank_event'])


    # Define a function to read the souces, targets, values and time from event to next_event:
    def update_source_target(user):
        try:
            # user.name[0] is the user's user_id; user.name[1] is the rank of each action
            # 1st we retrieve the source and target's indices from nodes_dict
            source_index = output['nodes_dict'][user.name[1]]['sources_index'][output['nodes_dict']
            [user.name[1]]['sources'].index(user['event_name'].values[0])]
            target_index = output['nodes_dict'][user.name[1] + 1]['sources_index'][output['nodes_dict']
            [user.name[1] + 1]['sources'].index(user['next_event'].values[0])]

            # If this source is already in links_dict...
            if source_index in output['links_dict']:
                # ...and if this target is already associated to this source...
                if target_index in output['links_dict'][source_index]:
                    # ...then we increment the count of users with this source/target pair by 1, and keep track of the time from source to target
                    output['links_dict'][source_index][target_index]['unique_users'] += 1
                    output['links_dict'][source_index][target_index]['avg_time_to_next'] += user['time_to_next'].values[
                        0]
                # ...but if the target is not already associated to this source...
                else:
                    # ...we create a new key for this target, for this source, and initiate it with 1 user and the time from source to target
                    output['links_dict'][source_index].update({target_index:
                        dict(
                            {'unique_users': 1,
                             'avg_time_to_next': user['time_to_next'].values[0]}
                        )
                    })
            # ...but if this source isn't already available in the links_dict, we create its key and the key of this source's target, and we initiate it with 1 user and the time from source to target
            else:
                output['links_dict'].update({source_index: dict({target_index: dict(
                    {'unique_users': 1, 'avg_time_to_next': user['time_to_next'].values[0]})})})
        except Exception as e:
            pass


    # Apply the function to your grouped Pandas object:
    grouped.apply(lambda user: update_source_target(user))

    ############################### Next Script ##################################
    targets = []
    sources = []
    values = []
    time_to_next = []

    for source_key, source_value in output['links_dict'].items():
        for target_key, target_value in output['links_dict'][source_key].items():
            sources.append(source_key)
            targets.append(target_key)
            values.append(target_value['unique_users'])
            time_to_next.append(str(pd.to_timedelta(
                target_value['avg_time_to_next'] / target_value['unique_users'])).split('.')[
                                    0])  # Split to remove the milliseconds information

    labels = []
    colors = []
    for key, value in output['nodes_dict'].items():
        labels = labels + list(output['nodes_dict'][key]['sources'])
        colors = colors + list(output['nodes_dict'][key]['color'])

    for idx, color in enumerate(colors):
        colors[idx] = "rgb" + str(color) + ""

    ################################## Final Script of Plotting ###############################
    import plotly.graph_objects as go
    import chart_studio.plotly as py
    from plotly.offline import iplot
    import plotly
    import webbrowser

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            thickness=10,  # default is 20
            line=dict(color="black", width=0.5),
            label=labels,
            color=colors
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            label=time_to_next,
            hovertemplate='%{value} unique users went from %{source.label} to %{target.label}.<br />' +
                          '<br />It took them %{label} in average.<extra></extra>',
        ))])

    fig.update_layout(autosize=True, title_text="Medium app", font=dict(size=15), plot_bgcolor='white')
    fig.show()
    #
    # urL = 'https://www.google.com'
    # firefox_path = "C:\\Program Files\\Mozilla Firefox\\firefox.exe"
    # webbrowser.register('firefox', None, webbrowser.BackgroundBrowser(firefox_path), 1)
    # webbrowser.get('firefox').open_new_tab(urL)