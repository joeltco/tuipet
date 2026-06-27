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

public final class SoundConfig {
    public static float _masterVolume;
    public static float _musicVolume;
    public static float _effectsVolume;
    public static String _click;
    public static String _select;
    public static String _cancel;
    public static String _error;
    public static String _hatch;
    public static String _call;
    public static String _eat;
    public static String _wash;
    public static String _poop;
    public static String _smallPoop;
    public static String _largePoop;
    public static String _flush;
    public static String _happy;
    public static String _unhappy;
    public static String _angry;
    public static String _win;
    public static String _lose;
    public static String _attack;
    public static String _strongAttack;
    public static String _strongHit;
    public static String _retreatScramble;
    public static String _retreatDash;
    public static String _addBits;
    public static String _subtractBits;
    public static String _unlockDNA;
    public static String _unlockConsumable;
    public static String _perfectWinsInc;
    public static String _healthInc;
    public static String _inheritChipShrink;
    public static String _inheritParentGrow;
    public static String _inheritParentShrink;
    public static String _inheritMove;
    public static String _inheritCollide;
    public static String _digicorePulse;
    public static String _digicoreExpand;
    public static String _silhouetteFade;
    public static String _itemEvolveLoop;
    public static String _evolve;
    public static String _teleportDisappear;
    public static String _teleportShrink;
    public static String _teleportDepart;
    public static String _teleportArrive;
    public static String _teleportExpand;
    public static String _teleportAppear;
    public static String _freezeLoop;
    public static String _dying;
    public static String _dieLoop;
    public static String _hitButton;
    public static String _battleHPDecrease;
    public static String _battleHPIncrease;
    public static String _populateTourneyRoster;
    public static String _adventureLifeDecrease;
    public static String _adventureLifeIncrease;
    public static String _dnaChargeInsert;
    public static String _lastBite;
    public static String _useBandage;
    public static String _lastBandage;
    public static String _adventureLifeRecover;
    public static String _hitBall;
    public static String _discoverEnemy;
    public static String _zonePulse;
    public static String _zonePulseLoop;
    public static String _whaTransportFall;
    public static String _flyTransportFall;
    public static String _refuse;
    public static String _whaTransportSurprise;
    public static String _whaTransportEject;
    public static String _transportLiftOff;
    public static String _discoverConsumable;
    public static String _attention;
    public static String _xProgramShrink;
    public static String _dnaWash;
    public static String _whaTransportUseTicket;
    public static String _transportUseTicket;
    public static String _xProgramHit;
    public static String _bossDeath;
    public static String _dnaDrop;
    public static String _heal;
    public static String _npcFight;
    public static String _bossDying;
    public static String _turretShoot;
    public static String _tourneyStart;
    public static String _bossParade;
    public static String _dnaWashCollide;
    public static String _jogressFlash;
    public static String _jogressStart;
    public static String _battleFlash;
    public static String _startBattle;
    public static String _startMenuDayLoop;
    public static String _startMenuNightLoop;
    public static String _jogressLoop;
    public static String _unfreezeLoop;
    public static String _xProgramDescendLoop;
    public static String _jogressMismatch;
    public static String _refuseSurrender;
    public static String _nextKeyboardCharacter;
    public static String _previousKeyboardCharacter;
    public static String _selectKeyboardCharacter;
    public static String _cancelKeyboardCharacter;
    public static String _shortThunder;
    public static String _longThunder;
    public static String _sharpThunder;
    public static String _heavyRainLoop;
    public static String _rainLoop;
    public static String _drizzleLoop;
    public static String _heavySnowLoop;
    public static String _snowLoop;
    public static String _lightSnowLoop;
    public static String _attackHit;
    public static String _badHealthJeer;
    public static String _trainTimer;
    public static String _studyProgress;
    public static String _studyStart;
    public static String _playingInteract;
    public static String _rideJump;
    public static String _lifting;
    public static String _bathing;
    public static String _showerOn;
    public static String _showerWash;
    public static String _showerEnd;
    public static String _interact;
    public static String _xylophone;
    public static String _xylophone2;
    public static String _pour;
    public static String _ovenSet;
    public static String _ovenFinish;
    public static String _tvStatic;
    public static String _monitorBeep;
    public static String _computerFlash;

    private SoundConfig() {
    }

    private static void readConfigInfo(String[] info) {
        try {
            _masterVolume = Float.parseFloat(info[0]);
            _musicVolume = Float.parseFloat(info[1]);
            _effectsVolume = Float.parseFloat(info[2]);
            _click = SoundConfig.getName(info, 3);
            _select = SoundConfig.getName(info, 4);
            _cancel = SoundConfig.getName(info, 5);
            _error = SoundConfig.getName(info, 6);
            _hatch = SoundConfig.getName(info, 7);
            _call = SoundConfig.getName(info, 8);
            _eat = SoundConfig.getName(info, 9);
            _wash = SoundConfig.getName(info, 10);
            _poop = SoundConfig.getName(info, 11);
            _happy = SoundConfig.getName(info, 12);
            _unhappy = SoundConfig.getName(info, 13);
            _angry = SoundConfig.getName(info, 14);
            _win = SoundConfig.getName(info, 15);
            _lose = SoundConfig.getName(info, 16);
            _attack = SoundConfig.getName(info, 17);
            _strongAttack = SoundConfig.getName(info, 18);
            _strongHit = SoundConfig.getName(info, 19);
            _retreatScramble = SoundConfig.getName(info, 20);
            _retreatDash = SoundConfig.getName(info, 21);
            _addBits = SoundConfig.getName(info, 22);
            _subtractBits = SoundConfig.getName(info, 23);
            _unlockDNA = SoundConfig.getName(info, 24);
            _unlockConsumable = SoundConfig.getName(info, 25);
            _perfectWinsInc = SoundConfig.getName(info, 26);
            _healthInc = SoundConfig.getName(info, 27);
            _inheritChipShrink = SoundConfig.getName(info, 28);
            _inheritParentGrow = SoundConfig.getName(info, 29);
            _inheritParentShrink = SoundConfig.getName(info, 30);
            _inheritMove = SoundConfig.getName(info, 31);
            _inheritCollide = SoundConfig.getName(info, 32);
            _digicorePulse = SoundConfig.getName(info, 33);
            _digicoreExpand = SoundConfig.getName(info, 34);
            _silhouetteFade = SoundConfig.getName(info, 35);
            _itemEvolveLoop = SoundConfig.getName(info, 36);
            _evolve = SoundConfig.getName(info, 37);
            _teleportDisappear = SoundConfig.getName(info, 38);
            _teleportShrink = SoundConfig.getName(info, 39);
            _teleportDepart = SoundConfig.getName(info, 40);
            _teleportArrive = SoundConfig.getName(info, 41);
            _teleportExpand = SoundConfig.getName(info, 42);
            _teleportAppear = SoundConfig.getName(info, 43);
            _freezeLoop = SoundConfig.getName(info, 44);
            _dying = SoundConfig.getName(info, 45);
            _dieLoop = SoundConfig.getName(info, 46);
            _hitButton = SoundConfig.getName(info, 47);
            _battleHPDecrease = SoundConfig.getName(info, 48);
            _battleHPIncrease = SoundConfig.getName(info, 49);
            _populateTourneyRoster = SoundConfig.getName(info, 50);
            _adventureLifeDecrease = SoundConfig.getName(info, 51);
            _adventureLifeIncrease = SoundConfig.getName(info, 52);
            _dnaChargeInsert = SoundConfig.getName(info, 53);
            _lastBite = SoundConfig.getName(info, 54);
            _useBandage = SoundConfig.getName(info, 55);
            _lastBandage = SoundConfig.getName(info, 56);
            _adventureLifeRecover = SoundConfig.getName(info, 57);
            _hitBall = SoundConfig.getName(info, 58);
            _discoverEnemy = SoundConfig.getName(info, 59);
            _zonePulse = SoundConfig.getName(info, 60);
            _zonePulseLoop = SoundConfig.getName(info, 61);
            _whaTransportFall = SoundConfig.getName(info, 62);
            _flyTransportFall = SoundConfig.getName(info, 63);
            _refuse = SoundConfig.getName(info, 64);
            _whaTransportSurprise = SoundConfig.getName(info, 65);
            _whaTransportEject = SoundConfig.getName(info, 66);
            _transportLiftOff = SoundConfig.getName(info, 67);
            _attention = SoundConfig.getName(info, 68);
            _xProgramShrink = SoundConfig.getName(info, 69);
            _dnaWash = SoundConfig.getName(info, 70);
            _whaTransportUseTicket = SoundConfig.getName(info, 71);
            _transportUseTicket = SoundConfig.getName(info, 72);
            _xProgramHit = SoundConfig.getName(info, 73);
            _bossDeath = SoundConfig.getName(info, 74);
            _dnaDrop = SoundConfig.getName(info, 75);
            _heal = SoundConfig.getName(info, 76);
            _npcFight = SoundConfig.getName(info, 77);
            _bossDying = SoundConfig.getName(info, 78);
            _turretShoot = SoundConfig.getName(info, 79);
            _tourneyStart = SoundConfig.getName(info, 80);
            _bossParade = SoundConfig.getName(info, 81);
            _dnaWashCollide = SoundConfig.getName(info, 82);
            _jogressFlash = SoundConfig.getName(info, 83);
            _jogressStart = SoundConfig.getName(info, 84);
            _battleFlash = SoundConfig.getName(info, 85);
            _startBattle = SoundConfig.getName(info, 86);
            _startMenuDayLoop = SoundConfig.getName(info, 87);
            _startMenuNightLoop = SoundConfig.getName(info, 88);
            _jogressLoop = SoundConfig.getName(info, 89);
            _unfreezeLoop = SoundConfig.getName(info, 90);
            _xProgramDescendLoop = SoundConfig.getName(info, 91);
            _jogressMismatch = SoundConfig.getName(info, 92);
            _refuseSurrender = SoundConfig.getName(info, 93);
            _nextKeyboardCharacter = SoundConfig.getName(info, 94);
            _previousKeyboardCharacter = SoundConfig.getName(info, 95);
            _selectKeyboardCharacter = SoundConfig.getName(info, 96);
            _cancelKeyboardCharacter = SoundConfig.getName(info, 97);
            _shortThunder = SoundConfig.getName(info, 98);
            _longThunder = SoundConfig.getName(info, 99);
            _sharpThunder = SoundConfig.getName(info, 100);
            _heavyRainLoop = SoundConfig.getName(info, 101);
            _rainLoop = SoundConfig.getName(info, 102);
            _drizzleLoop = SoundConfig.getName(info, 103);
            _heavySnowLoop = SoundConfig.getName(info, 104);
            _snowLoop = SoundConfig.getName(info, 105);
            _lightSnowLoop = SoundConfig.getName(info, 106);
            _discoverConsumable = SoundConfig.getName(info, 107);
            _attackHit = SoundConfig.getName(info, 108);
            _badHealthJeer = SoundConfig.getName(info, 109);
            _flush = SoundConfig.getName(info, 110);
            _smallPoop = SoundConfig.getName(info, 111);
            _largePoop = SoundConfig.getName(info, 112);
            _trainTimer = SoundConfig.getName(info, 113);
            _studyProgress = SoundConfig.getName(info, 114);
            _studyStart = SoundConfig.getName(info, 115);
            _playingInteract = SoundConfig.getName(info, 116);
            _rideJump = SoundConfig.getName(info, 117);
            _lifting = SoundConfig.getName(info, 118);
            _bathing = SoundConfig.getName(info, 119);
            _showerOn = SoundConfig.getName(info, 120);
            _showerWash = SoundConfig.getName(info, 121);
            _showerEnd = SoundConfig.getName(info, 122);
            _interact = SoundConfig.getName(info, 123);
            _xylophone = SoundConfig.getName(info, 124);
            _xylophone2 = SoundConfig.getName(info, 125);
            _pour = SoundConfig.getName(info, 126);
            _ovenSet = SoundConfig.getName(info, 127);
            _ovenFinish = SoundConfig.getName(info, 128);
            _tvStatic = SoundConfig.getName(info, 129);
            _monitorBeep = SoundConfig.getName(info, 130);
            _computerFlash = SoundConfig.getName(info, 131);
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static String getName(String[] info, int i) {
        if (info.length > i) {
            return info[i];
        }
        return "";
    }

    public static void loadConfig(String modFolder) {
        try (InputStream in = SoundConfig.class.getResourceAsStream(Utility.getExistingFileLoc(modFolder + "csv" + File.separator, "/View/", "soundConfig.csv"));
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
            SoundConfig.readConfigInfo(info.toArray(new String[info.size()]));
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }
}

