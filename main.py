from flask import Flask, render_template
from dash import dcc, html, Dash, no_update, callback_context
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from datetime import datetime
import soundfile as sf
import numpy as np
import librosa
import base64
import io

server = Flask(__name__)

app1 = Dash(__name__, server=server, url_base_pathname='/amplitude/')
app2 = Dash(__name__, server=server, url_base_pathname='/spectrogram/')

app1.layout = html.Div([
    html.H1('Amplitude Analysis', style={'textAlign': 'center'}),
    html.Div(
        dcc.Upload(
            id='upload-audio',
            children=html.Button('Upload Audio File', style={'fontSize': 20}),
            multiple=False
        ),
        style={'textAlign': 'center', 'marginBottom': '20px'}
    ),
    html.Div(id='audio-player', style={'textAlign': 'center'}),  
    dcc.Loading(
        id='loading',
        type='default',
        children=dcc.Graph(id='amplitude-plot', config={
            'modeBarButtonsToAdd': ['drawrect', 'eraseshape', 'zoom', 'zoomIn', 'zoomOut', 'resetScale2d'],
            'displaylogo': False
        })
    ),
    html.H3('There are two ways to set the start and end times here:', style={'textAlign': 'center'}),
    html.H3([html.Span('1.', style={'color': 'red'}), html.Span('', style={'display': 'inline-block', 'width': '5px'}), 'Manually enter start and end time values,',
             html.Span('', style={'display': 'inline-block', 'width': '40px'}),
             html.Span('2.', style={'color': 'red'}), html.Span('', style={'display': 'inline-block', 'width': '5px'}), 'Use the Draw rectangle tool in the upper right corner to make a selection.'], style={'textAlign': 'center'}),
    html.Div([
        'Start Time (s): ',
        dcc.Input(id='start-time', type='number', value=0, step=0.0001, style={'fontSize': 20, 'height': '25px', 'width': '100px'}),
        html.Span(' ', style={'margin': '0 10px'}),
        ' End Time (s): ',
        dcc.Input(id='end-time', type='number', value=0, step=0.0001, style={'fontSize': 20, 'height': '25px', 'width': '100px'}),
        html.Span(' ', style={'margin': '0 10px'}),
        html.Button('Confirm', id='confirm-button', n_clicks=0, style={'fontSize': 20, 'height': '30px'})
    ], style={'textAlign': 'center', 'fontSize': 20, 'marginBottom': 10}),
    html.Div(id='output-container', style={'textAlign': 'center', 'fontSize': 20}),
    
    dcc.Loading(
        id='loading-magnitude',
        type='default',
        children=dcc.Graph(id='fft-magnitude-plot', config={
            'modeBarButtonsToAdd': ['eraseshape', 'zoom', 'zoomIn', 'zoomOut', 'resetScale2d'],
            'displaylogo': False
        })
    ),
    dcc.Loading(
        id='loading-phase',
        type='default',
        children=dcc.Graph(id='fft-phase-plot')
    ),
    dcc.Loading(
        id='loading-inverse',
        type='default',
        children=dcc.Graph(id='inverse-amplitude-plot')
    ),
    dcc.Store(id='line-color-update', data=False)
])

app2.layout = html.Div([
    html.H1('Audio Spectrogram Viewer', style={'textAlign': 'center'}),
    dcc.Upload(
        id='upload-audio',
        children=html.Button('Upload Audio File', style={'fontSize': 20}),
        style={'textAlign': 'center', 'marginBottom': '5px'}
    ),
    html.Div(id='audio-player', style={'textAlign': 'center'}),
    dcc.Graph(
        id='spectrogram',
        config={
            'modeBarButtonsToAdd': ['drawrect', 'eraseshape', 'zoom', 'zoomIn', 'zoomOut', 'resetScale2d'],
            'displaylogo': False,
        }
    ),
    html.Button('Move Line and Play Audio', id='move-line-button', style={'fontSize': 20,'marginBottom': '10px'}),
    html.H3('There are two ways to set the start and end times here:', style={'textAlign': 'center'}),
    html.H3([html.Span('1.', style={'color': 'red'}), html.Span('', style={'display': 'inline-block', 'width': '5px'}), 'Manually enter start and end time values,',
             html.Span('', style={'display': 'inline-block', 'width': '40px'}),
             html.Span('2.', style={'color': 'red'}), html.Span('', style={'display': 'inline-block', 'width': '5px'}), 'Use the Draw rectangle tool in the upper right corner to make a selection.'], style={'textAlign': 'center'}),
    html.Div([
        'Start Time (s): ',
        dcc.Input(id='start-time-input', type='number', value=0, step=0.0001, style={'fontSize': 20, 'height': '25px', 'width': '100px'}),
        ' End Time (s): ',
        dcc.Input(id='end-time-input', type='number', value=0, step=0.0001, style={'fontSize': 20, 'height': '25px', 'width': '100px'}),
        html.Button('Confirm', id='confirm-button', n_clicks=0, style={'fontSize': 20, 'height': '30px'})
    ], style={'textAlign': 'center', 'fontSize': 20, 'marginBottom': 10}),
    html.Div(id='clipped-audio-player', style={'textAlign': 'center'}),
    dcc.Graph(id='clipped-spectrogram', style={'width': '90%', 'margin': '0 auto'}),
    html.Button('Move Clipped Line and Play Audio', id='move-clipped-line-button', style={'fontSize': 20}),
    html.Button(id='hidden-play-button', style={'display': 'none'}), 
    html.Button(id='hidden-clipped-play-button', style={'display': 'none'}), 
    dcc.Interval(
        id='interval-component',
        interval=100,
        n_intervals=0,
        disabled=True
    ),
    dcc.Interval(
        id='clipped-interval-component',
        interval=100,
        n_intervals=0,
        disabled=True
    ),
    dcc.Store(id='line-position', data={'x': 0, 'moving': False}),
    dcc.Store(id='clipped-line-position', data={'x': 0, 'moving': False}),
    dcc.Store(id='audio-content', data=''),
    dcc.Store(id='start-time', data={'start': None}),
    dcc.Store(id='clip-time', data={'start': 0, 'end': 0}),
    dcc.Store(id='clipped-start-time', data={'start': None})
], style={'textAlign': 'center'})

def parse_contents1(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    audio_data, sr = librosa.load(io.BytesIO(decoded), sr=None)
    
    # Calculate the amplitude
    amplitude = audio_data
    time = np.linspace(0, len(audio_data) / sr, num=len(audio_data))

    # Convert amplitude and time to standard Python float
    amplitude = amplitude.astype(float)
    time = time.astype(float)

    # Create the initial amplitude plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time, y=amplitude, mode='lines', name='Amplitude'))
    fig.update_layout(
        title=dict(text='Audio Waveform', font=dict(weight='bold')),
        xaxis_title='Time (s)',
        yaxis_title='Amplitude',
        dragmode='drawrect',
        newshape=dict(
            line=dict(color='red')
        )
    )
    
    return fig, time, amplitude, sr, content_string

@app1.callback(
    Output('line-color-update', 'data'),
    [Input('confirm-button', 'n_clicks')],
    [State('line-color-update', 'data')]
)
def set_line_color_update(n_clicks, current_status):
    if n_clicks > 0:
        return not current_status
    return current_status

@app1.callback(
    [Output('amplitude-plot', 'figure'),
     Output('audio-player', 'children'),
     Output('start-time', 'value'),
     Output('end-time', 'value')],
    [Input('upload-audio', 'contents'),
     Input('confirm-button', 'n_clicks'),
     Input('amplitude-plot', 'relayoutData')],
    [State('amplitude-plot', 'figure')]
)
def update_amplitude_plot(contents, n_clicks, relayoutData, figure):
    ctx = callback_context

    if ctx.triggered and ctx.triggered[0]['prop_id'].split('.')[0] == 'upload-audio':
        if contents is not None:
            amplitude_fig, time, amplitude, sr, content_string = parse_contents1(contents)
            amplitude_fig.update_layout(
                shapes=[]
            )
            audio_player = html.Audio(
                src=f'data:audio/wav;base64,{content_string}',
                controls=True,
                style={'width': '25%'}
            )
            return amplitude_fig, audio_player, no_update, no_update

    if ctx.triggered and ctx.triggered[0]['prop_id'].split('.')[0] == 'confirm-button':
        if n_clicks > 0 and figure and 'layout' in figure and 'shapes' in figure['layout']:
            for shape in figure['layout']['shapes']:
                shape['line']['color'] = 'rgba(255, 0, 0, 0)'
                shape['line']['width'] = 1
            return figure, no_update, no_update, no_update

    if ctx.triggered and ctx.triggered[0]['prop_id'].split('.')[0] == 'amplitude-plot':
        if 'shapes' in relayoutData:
            shape = relayoutData['shapes'][-1]  
            x0, x1 = shape['x0'], shape['x1']

            if figure and 'layout' in figure and 'yaxis' in figure['layout']:
                yaxis_range = figure['layout']['yaxis']['range']
                y0 = yaxis_range[0]
                y1 = yaxis_range[1]
                
                shape['y0'] = y0
                shape['y1'] = y1

                figure['layout']['shapes'][-1]['y0'] = y0
                figure['layout']['shapes'][-1]['y1'] = y1

                start_time = float(format(min(x0, x1), '.5f'))
                end_time = float(format(max(x0, x1), '.5f'))
                return figure, no_update, start_time, end_time

    if figure is not None:
        return figure, no_update, no_update, no_update

    return go.Figure(), '', no_update, no_update

@app1.callback(
    [Output('output-container', 'children'),
     Output('fft-magnitude-plot', 'figure'),
     Output('fft-phase-plot', 'figure'),
     Output('inverse-amplitude-plot', 'figure')],
    [Input('confirm-button', 'n_clicks')],
    [State('amplitude-plot', 'figure'),
     State('start-time', 'value'),
     State('end-time', 'value')]
)
def update_fft_and_inverse_plots(n_clicks, figure, start_time, end_time):
    if figure is None or 'data' not in figure or len(figure['data']) == 0:
        return 'Upload an audio file to analyze.', go.Figure(), go.Figure(), go.Figure()

    time = np.array(figure['data'][0]['x'])
    amplitude = np.array(figure['data'][0]['y'])
    sr = 1 / (time[1] - time[0])
    
    x0, x1 = None, None

    if n_clicks > 0 and start_time is not None and end_time is not None:
        x0 = start_time
        x1 = end_time

    if x0 is not None and x1 is not None:
        if x0 > x1:
            x0, x1 = x1, x0

        selected_points = [{'time': time[i], 'amplitude': amplitude[i]} for i in range(len(time)) if x0 <= time[i] <= x1]

        amplitudes = np.array([point['amplitude'] for point in selected_points])
        
        if len(amplitudes) % 2 != 0:
            amplitudes = np.append(amplitudes, 0)

        N = len(amplitudes)
        yf_segment = np.fft.fft(amplitudes)
        xf_segment = np.fft.fftfreq(N, 1 / sr)

        idx = np.arange(0, N // 2)
        xf_segment = xf_segment[idx]
        yf_segment_magnitude = np.abs(yf_segment)
        yf_segment_phase = np.angle(yf_segment)

        fft_magnitude_fig = go.Figure()
        fft_magnitude_fig.add_trace(go.Scatter(x=xf_segment, y=yf_segment_magnitude[idx], mode='lines', name='Magnitude'))
        fft_magnitude_fig.update_layout(
            title=dict(text='<span style="color:red"> DFT: </span> Frequency-Domain Signal (Magnitude Spectrum)', font=dict(weight='bold')),
            xaxis_title='Frequency (Hz)',
            yaxis_title='Magnitude',
            paper_bgcolor='rgb(249,249,249)'
        )

        fft_phase_fig = go.Figure()
        fft_phase_fig.add_trace(go.Scatter(x=xf_segment, y=yf_segment_phase[idx], mode='lines', name='Phase'))
        fft_phase_fig.update_layout(
            title=dict(text='<span style="color:red"> DFT: </span> Frequency-Domain Signal (Phase Spectrum)', font=dict(weight='bold')),
            xaxis_title='Frequency (Hz)',
            yaxis_title='Phase (radians)',
            paper_bgcolor='rgb(249,249,249)'
        )

        X_reconstructed = yf_segment_magnitude * np.exp(1j * yf_segment_phase)
        x_reconstructed = np.fft.ifft(X_reconstructed).real
        time_inverse = np.linspace(0, len(x_reconstructed) / sr, num=len(x_reconstructed))
        inverse_amplitude_fig = go.Figure()
        inverse_amplitude_fig.add_trace(go.Scatter(x=time_inverse, y=x_reconstructed, mode='lines', name='Inverse Amplitude'))
        inverse_amplitude_fig.update_layout(
            title=dict(text='Reconstructed Time-Domain Signal from <span style="color:red"> IDFT: </span> ', font=dict(weight='bold')),
            xaxis_title='Time (s)',
            yaxis_title='Amplitude'
        )

        return f'Selected Region: Start = {x0:.5f}, End = {x1:.5f}. Number of points selected: {len(selected_points)}.', fft_magnitude_fig, fft_phase_fig, inverse_amplitude_fig

    return 'Select a region to see the coordinates.', go.Figure(), go.Figure(), go.Figure()

#===========================
def parse_contents2(contents):
    if contents:
        content_type, content_string = contents.split(',', 1)
        return base64.b64decode(content_string)
    return None

def create_spectrogram_figure(y, sr, duration, line_position, title, start_time=None, end_time=None):
    S = librosa.feature.melspectrogram(y=y, sr=sr)
    S_dB = librosa.power_to_db(S, ref=np.max)
    
    fig = go.Figure()

    if start_time is not None and end_time is not None:
        x_values = np.linspace(start_time, end_time, S_dB.shape[1])
        x_axis_range = [start_time, end_time]
        tickvals = np.linspace(start_time, end_time, 10)
    else:
        x_values = np.linspace(0, duration, S_dB.shape[1])
        x_axis_range = [0, duration]
        tickvals = np.linspace(0, duration, 10)
    
    fig.add_trace(go.Heatmap(
        z=S_dB,
        x=x_values,
        y=librosa.fft_frequencies(sr=sr, n_fft=S.shape[0]*2-1),
        colorscale='Plasma'
    ))

    fig.add_trace(go.Scatter(
        x=[line_position['x'], line_position['x']],
        y=[0, np.max(librosa.fft_frequencies(sr=sr, n_fft=S.shape[0]*2-1))],
        mode='lines',
        line=dict(color='white', width=4),
        name='Red Line'
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(weight='bold')),
        xaxis=dict(
            title='Time (s)',
            range=x_axis_range,
            tickvals=tickvals,
            ticktext=[f'{tick:.3f}' for tick in tickvals]
        ),
        yaxis=dict(
            title='Frequency (Hz)',
            range=[0, np.max(librosa.fft_frequencies(sr=sr, n_fft=S.shape[0]*2-1))]
        ),
        dragmode='drawrect',
        newshape=dict(line=dict(color='white'))
    )
    
    return fig

@app2.callback(
    [Output('audio-player', 'children'),
     Output('spectrogram', 'figure'),
     Output('interval-component', 'disabled'),
     Output('line-position', 'data'),
     Output('interval-component', 'interval'),
     Output('audio-content', 'data'),
     Output('start-time', 'data'),
     Output('clip-time', 'data'),
     Output('clipped-audio-player', 'children'),
     Output('start-time-input', 'value'),
     Output('end-time-input', 'value')],
    [Input('upload-audio', 'contents'),
     Input('move-line-button', 'n_clicks'),
     Input('interval-component', 'n_intervals'),
     Input('confirm-button', 'n_clicks'),
     Input('spectrogram', 'relayoutData')],
    [State('line-position', 'data'),
     State('audio-content', 'data'),
     State('start-time', 'data'),
     State('start-time-input', 'value'),
     State('end-time-input', 'value'),
     State('clip-time', 'data')]
)
def update_output(contents, move_clicks, n_intervals, confirm_clicks, relayoutData, line_position, audio_content, start_time, start_time_input, end_time_input, clip_time):
    ctx = callback_context
    if not ctx.triggered:
        return '', go.Figure(), True, line_position, no_update, no_update, start_time, clip_time, no_update, no_update, no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'upload-audio' and contents:
        data = parse_contents2(contents)
        y, sr = librosa.load(io.BytesIO(data), sr=None)
        duration = len(y) / sr

        fig = create_spectrogram_figure(y, sr, duration, line_position, '<span style="color:red"> Spectrogram </span> of audio signal')

        audio_src = f'data:audio/wav;base64,{contents.split(",")[1]}'
        audio_player = html.Audio(src=audio_src, controls=True, id='audio-element', style={'width': '90%'})
        return audio_player, fig, True, line_position, no_update, contents, {'start': None}, {'start': 0, 'end': duration}, no_update, no_update, no_update

    elif trigger_id == 'move-line-button' and move_clicks:
        start_time = {'start': datetime.now().timestamp()}
        return no_update, no_update, False, {'x': 0, 'moving': True}, no_update, audio_content, start_time, clip_time, no_update, no_update, no_update

    elif trigger_id == 'interval-component' and line_position['moving']:
        data = parse_contents2(audio_content)
        y, sr = librosa.load(io.BytesIO(data), sr=None)
        duration = len(y) / sr

        current_time = datetime.now().timestamp()
        elapsed_time = current_time - start_time['start']

        new_x = min(elapsed_time, duration)
        if new_x >= duration:
            new_x = duration
            line_position['moving'] = False

        line_position['x'] = new_x

        fig = create_spectrogram_figure(y, sr, duration, line_position, '<span style="color:red"> Spectrogram </span> of audio signal')

        return no_update, fig, not line_position['moving'], line_position, no_update, no_update, start_time, clip_time, no_update, no_update, no_update

    elif trigger_id == 'confirm-button' and confirm_clicks:
        data = parse_contents2(audio_content)
        y, sr = librosa.load(io.BytesIO(data), sr=None)

        clip_time = {'start': start_time_input, 'end': end_time_input}
        clipped_y = y[int(start_time_input * sr):int(end_time_input * sr)]
        clipped_duration = len(clipped_y) / sr

        fig = create_spectrogram_figure(y, sr, len(y) / sr, line_position, '<span style="color:red"> Spectrogram </span> of audio signal')
        clipped_fig = create_spectrogram_figure(clipped_y, sr, clipped_duration, {'x': 0, 'moving': False}, 'Clipped spectrogram', start_time_input, end_time_input)

        clipped_audio_bytes = io.BytesIO()
        sf.write(clipped_audio_bytes, clipped_y, sr, format='wav')
        clipped_audio_bytes.seek(0)
        clipped_audio_b64 = base64.b64encode(clipped_audio_bytes.read()).decode('utf-8')

        clipped_audio_player = html.Audio(
            src=f'data:audio/wav;base64,{clipped_audio_b64}',
            controls=True,
            id='clipped-audio-element',
            style={'width': '70%'}
        )

        return no_update, fig, no_update, line_position, no_update, audio_content, start_time, clip_time, clipped_audio_player, no_update, no_update

    elif trigger_id == 'spectrogram' and 'shapes' in relayoutData:
        shape = relayoutData['shapes'][-1]  
        x0, x1 = shape['x0'], shape['x1']

        start_time_input = float(format(min(x0, x1), '.3f'))
        end_time_input = float(format(max(x0, x1), '.3f'))

        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, start_time_input, end_time_input

    return no_update, no_update, True, line_position, no_update, no_update, start_time, clip_time, no_update, no_update, no_update

@app2.callback(
    Output('clipped-spectrogram', 'figure'),
    [Input('clip-time', 'data'),
     Input('clipped-line-position', 'data')],
    [State('audio-content', 'data')]
)
def update_clipped_spectrogram(clip_time, clipped_line_position, audio_content):
    if clip_time['start'] is None or clip_time['end'] is None:
        return go.Figure()

    data = parse_contents2(audio_content)
    if data is None:
        return go.Figure()  # Return an empty figure if no audio content is available

    y, sr = librosa.load(io.BytesIO(data), sr=None)

    clipped_y = y[int(clip_time['start'] * sr):int(clip_time['end'] * sr)]
    clipped_duration = len(clipped_y) / sr

    clipped_fig = create_spectrogram_figure(clipped_y, sr, clipped_duration, clipped_line_position, 'Clipped spectrogram', clip_time['start'], clip_time['end'])

    return clipped_fig

@app2.callback(
    [Output('clipped-interval-component', 'disabled'),
     Output('clipped-line-position', 'data'),
     Output('clipped-start-time', 'data')],
    [Input('move-clipped-line-button', 'n_clicks'),
     Input('clipped-interval-component', 'n_intervals')],
    [State('clipped-line-position', 'data'),
     State('clip-time', 'data'),
     State('clipped-start-time', 'data')]
)
def move_clipped_line(n_clicks, n_intervals, clipped_line_position, clip_time, clipped_start_time):
    ctx = callback_context
    if not ctx.triggered:
        return True, clipped_line_position, clipped_start_time

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'move-clipped-line-button' and n_clicks:
        clipped_start_time = {'start': datetime.now().timestamp()}
        return False, {'x': clip_time['start'], 'moving': True}, clipped_start_time

    elif trigger_id == 'clipped-interval-component' and clipped_line_position['moving']:
        current_time = datetime.now().timestamp()
        elapsed_time = current_time - clipped_start_time['start']
        clipped_duration = clip_time['end'] - clip_time['start']

        new_x = min(clip_time['start'] + elapsed_time, clip_time['end'])
        if new_x >= clip_time['end']:
            new_x = clip_time['end']
            clipped_line_position['moving'] = False

        clipped_line_position['x'] = new_x

        return not clipped_line_position['moving'], clipped_line_position, clipped_start_time

    return True, clipped_line_position, clipped_start_time

@app2.callback(
    Output('hidden-play-button', 'n_clicks'),
    [Input('move-line-button', 'n_clicks')]
)
def play_audio_on_button_click(n_clicks):
    if n_clicks:
        return 1
    return no_update

@app2.callback(
    Output('hidden-clipped-play-button', 'n_clicks'),
    [Input('move-clipped-line-button', 'n_clicks')]
)
def play_clipped_audio_on_button_click(n_clicks):
    if n_clicks:
        return 1
    return no_update

app2.clientside_callback(
    """
    function(n_clicks) {
        var audio = document.getElementById('audio-element');
        if(audio) {
            audio.currentTime = 0;
            audio.play();
        }
        return '';
    }
    """,
    Output('hidden-play-button', 'children'),
    [Input('hidden-play-button', 'n_clicks')]
)

app2.clientside_callback(
    """
    function(n_clicks) {
        var audio = document.getElementById('clipped-audio-element');
        if(audio) {
            audio.currentTime = 0;
            audio.play();
        }
        return '';
    }
    """,
    Output('hidden-clipped-play-button', 'children'),
    [Input('hidden-clipped-play-button', 'n_clicks')]
)

@server.route('/')
def index():
    return render_template('index.html')

@server.route('/amplitude.html')
def render_analysis():
    return app1.index()

@server.route('/spectrogram.html')
def render_spectrogram():
    return app2.index()

if __name__ == '__main__':
    server.run(debug=False)
