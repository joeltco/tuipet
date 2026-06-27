/*
 * Decompiled with CFR 0.152.
 */
package View;

import Controller.Utility;
import java.io.BufferedReader;
import java.io.File;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;

public class ViewConfig {
    public static String _backgroundColor;
    public static boolean _transparentMenus;
    public static byte _fontSize;
    public static int _screenLoc;
    public static int _configLoc;
    public static int _aButton;
    public static int _bButton;
    public static int _cButton;
    public static int _dButton;
    public static boolean _enableKeyboardCursor;
    public static boolean _enableSingleClickClockSpeed;
    public static boolean _enableTextFieldKeyboardCursor;
    public static String _fulfilledReqColor;
    public static String _allDNAFulfilledColor;
    public static float _unfulfilledReqOpacity;
    public static int[] _habitatDimensions;
    public static float _backgroundOpacityChange;
    public static String _menuHighlightHex;
    public static int _menuHighlightAlpha;
    public static double _priorityDisplayCoefficient;
    public static int _firstClockSpeedKey;
    public static int _secondClockSpeedKey;
    public static int _thirdClockSpeedKey;
    public static int _fourthClockSpeedKey;
    public static int _pauseKey;
    public static int _characterKey;
    public static int _textFieldEscapeKey;
    public static int _rightClickKey;
    public static int _hideFastClock;
    public static int _maxLoopMod;
    public static double _loopModCoefficient;
    public static int _classicModeDigimon;
    public static int _hardModeDigimon;
    public static int _hardcoreModeDigimon;
    public static byte _trophyRecordsPageSize;

    private ViewConfig() {
    }

    private static void readConfigInfo(String[] info) {
        try {
            _backgroundColor = info[0];
            _transparentMenus = Boolean.parseBoolean(info[1]);
            _fontSize = Byte.parseByte(info[2]);
            _aButton = Integer.parseInt(info[3]);
            _bButton = Integer.parseInt(info[4]);
            _cButton = Integer.parseInt(info[5]);
            _dButton = Integer.parseInt(info[6]);
            _enableKeyboardCursor = Boolean.parseBoolean(info[7]);
            _enableTextFieldKeyboardCursor = Boolean.parseBoolean(info[8]);
            _fulfilledReqColor = info[9];
            _allDNAFulfilledColor = info[10];
            _unfulfilledReqOpacity = Float.parseFloat(info[11]);
            _habitatDimensions = new int[2];
            String[] d = info[12].split(";");
            ViewConfig._habitatDimensions[0] = Integer.parseInt(d[0]);
            ViewConfig._habitatDimensions[1] = Integer.parseInt(d[1]);
            _backgroundOpacityChange = Float.parseFloat(info[13]);
            _menuHighlightHex = info[14];
            _menuHighlightAlpha = Integer.parseInt(info[15]);
            _enableSingleClickClockSpeed = Boolean.parseBoolean(info[16]);
            _priorityDisplayCoefficient = Double.parseDouble(info[17]);
            _firstClockSpeedKey = Integer.parseInt(info[18]);
            _secondClockSpeedKey = Integer.parseInt(info[19]);
            _thirdClockSpeedKey = Integer.parseInt(info[20]);
            _fourthClockSpeedKey = Integer.parseInt(info[21]);
            _pauseKey = Integer.parseInt(info[22]);
            _characterKey = Integer.parseInt(info[23]);
            _textFieldEscapeKey = Integer.parseInt(info[24]);
            _rightClickKey = Integer.parseInt(info[25]);
            _hideFastClock = Integer.parseInt(info[26]);
            _maxLoopMod = Integer.parseInt(info[27]);
            _loopModCoefficient = Double.parseDouble(info[28]);
            _classicModeDigimon = Integer.parseInt(info[29]);
            _hardModeDigimon = Integer.parseInt(info[30]);
            _hardcoreModeDigimon = Integer.parseInt(info[31]);
            _trophyRecordsPageSize = Byte.parseByte(info[32]);
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void loadConfig(String modFolder) {
        try (InputStream in = Utility.getInputStream(modFolder + "csv" + File.separator, "/View/", "viewConfig.csv");
             BufferedReader reader = new BufferedReader(new InputStreamReader(in, "utf-8"));){
            ArrayList<String> info = new ArrayList<String>();
            String line = reader.readLine();
            while (line != null) {
                String[] detail = line.split(",");
                if (detail.length > 1) {
                    info.add(detail[1]);
                } else {
                    info.add("");
                }
                line = reader.readLine();
            }
            ViewConfig.readConfigInfo(info.toArray(new String[info.size()]));
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }
}

