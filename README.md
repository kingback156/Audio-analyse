# Audio-analyse
## Description
This project contains two demos. This first demo is a web application for performing amplitude analysis on audio files. It uses Flask as the web server and Dash for the interactive data visualization components. The application allows users to upload audio files, visualize their amplitude, select regions for DFT (Discrete Fourier Transform) analysis, and view inverse DFT (IDFT) plots. This second demo is a web application for visualizing audio spectrograms. The application allows users to upload audio files, view their spectrograms, and interact with features such as moving a line in sync with audio playback, and generating spectrograms for these clipped segments. Users can also play back both the original and clipped audio directly within the application.

<table>
  <tr>
    <td><img width="1044" alt="Snipaste_2024-03-17_15-46-47" src="https://github.com/user-attachments/assets/cf3f55f2-a5b5-4e6c-bb75-cf428793678c" scale=0.5></td>
    <td><img width="1057" alt="Snipaste_2024-03-17_15-47-37" src="https://github.com/user-attachments/assets/97ccd78f-2acb-4f36-be33-e3e56e8a4e88" scale=0.5></td>
    <td><img width="1044" alt="Snipaste_2024-03-17_15-46-47" src="https://github.com/user-attachments/assets/12969714-2147-4c77-a79d-9500d4241c46" scale=0.5></td>
    <td><img width="1044" alt="Snipaste_2024-03-17_15-46-47" src="https://github.com/user-attachments/assets/779a7791-6698-47a1-bdc1-a3dbb78b5ff6" scale=0.5></td>
  </tr>
</table>

## How to run
**Step 1:** Clone the repository:
```
git clone https://github.com/kingback156/Audio-analyse.git
```
**Step 2:** Please enter the following command in conda's virtual environment;
```
conda create --name analysis python=3.9
conda activate analysis
pip install -r requirements.txt
```
**Step 3:** Then, start the program with the following command：
```
python app.py
```
Open your browser and visit "http://127.0.0.1:5000" to access the application;

**Step 4:** After entering the homepage, click "Let's try it!" (as shown in Figure 1 above) to enter the analysis interface.

## A few notes
<img width="478" alt="Snipaste_2024-07-13_20-01-21" src="https://github.com/user-attachments/assets/d31abd3c-bc28-4e07-8341-2c79ed45ce0e">

- Enter the time period you want to check in the spectrogram and click "Confirm";
- You can of course also use the "Draw rectangle" tool to select the `Start Time` and the `End time`；
- Use the tool in the upper right corner to view the two graphs on the page in detail;
- The choice of audio data is unimportant, you can use the Test Cases I have provided for testing.

## Contact
If you have any question, please feel free to contact me. E-mail: ltl030529@163.com.
