/*
 * Decompiled with CFR 0.152.
 */
package Controller;

import Controller.BattleConnect;
import Controller.BattleHost;
import Controller.Checksum;
import Controller.JogressConnect;
import Controller.JogressHost;
import Controller.Utility;
import Model.Battle;
import Model.Config;
import Model.Consumable;
import Model.Controller;
import Model.CrashEntry;
import Model.DNA;
import Model.Enemy;
import Model.Enum;
import Model.FoodType;
import Model.Item;
import Model.MinLapsePacket;
import Model.PhysicalState;
import Model.ShopConsumable;
import Model.Tournament;
import Model.Trophy;
import Model.WorldMap;
import Model.Zone;
import View.EvolutionTree;
import View.KeyboardCursor;
import View.Shell;
import View.SoundConfig;
import View.SoundObj;
import View.SpriteAnim;
import View.ViewConfig;
import View.ViewUtil;
import java.awt.IllegalComponentStateException;
import java.awt.event.MouseEvent;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.logging.Level;
import java.util.logging.Logger;
import javax.swing.SwingUtilities;

public class ClockTic {
    private long _lastNanosecond;
    private long _lastCallNanosecond;
    private long _lastStepNanosecond;
    private final String MOD_FOLDER;
    private final boolean _tournamentVersion;
    private SoundObj _sounds;
    private KeyboardCursor _keyboard;
    private int _FPS;
    private boolean _gameRunning = true;
    private long _lastFPSTime;
    private final int TARGET_FPS = 60;
    private final long OPTIMAL_TIME = 16666666L;
    private final Controller _model;
    private SpriteAnim _view;
    private ArrayList<Shell> _shells = new ArrayList();
    private Battle _battle;
    private int _windowLocX;
    private int _windowLocY;
    private EvolutionTree _tree;
    private int _previousEnemy;
    private Enemy _jogressPartner;
    private Enum.Menu _currentMenu;
    private Enum.Menu _lastMenu;
    private Enum.Menu[] _menuHistory = new Enum.Menu[2];
    private BattleHost _hostBattle;
    private BattleConnect _connectBattle;
    private JogressHost _hostJogress;
    private JogressConnect _connectJogress;
    private byte _newScale;
    private int _numHits;
    private boolean _shieldActiveTop;
    private int _barSize = 0;
    private int _trainingRound;
    private int _trainingRoundsWon;
    private boolean _turnWait;

    public long getLastNanoSecond() {
        return this._lastNanosecond;
    }

    public int getTargetFPS() {
        return 60;
    }

    public Controller getModel() {
        return this._model;
    }

    public SpriteAnim getView() {
        return this._view;
    }

    public int getWindowLocX() {
        return this._windowLocX;
    }

    public void setWindowLocX(int newLoc) {
        this._windowLocX = newLoc;
    }

    public int getWindowLocY() {
        return this._windowLocY;
    }

    public void setWindowLocY(int newLoc) {
        this._windowLocY = newLoc;
    }

    public Battle getBattle() {
        return this._battle;
    }

    public BattleHost getHostBattle() {
        return this._hostBattle;
    }

    public BattleConnect getConnectBattle() {
        return this._connectBattle;
    }

    public JogressHost getHostJogress() {
        return this._hostJogress;
    }

    public JogressConnect getConnectJogress() {
        return this._connectJogress;
    }

    public boolean getShieldActiveTop() {
        return this._shieldActiveTop;
    }

    public Enum.Menu getCurrentMenu() {
        return this._currentMenu;
    }

    public void setCurrentMenu(Enum.Menu newMenu) {
        this._currentMenu = newMenu;
    }

    public Enum.State getCurrentState() {
        return this._model.getDigimon().getCurrentState();
    }

    public void setBarSize(int newSize) {
        this._barSize = newSize;
    }

    public int getBarSize() {
        return this._barSize;
    }

    public int getNumHits() {
        return this._numHits;
    }

    public void setNumHits(int i) {
        this._numHits = i;
    }

    public int getTrainingRound() {
        return this._trainingRound;
    }

    public void setTrainingRound(int i) {
        this._trainingRound = i;
    }

    public int getTrainingRoundsWon() {
        return this._trainingRoundsWon;
    }

    public void setTrainingRoundsWon(int i) {
        this._trainingRoundsWon = i;
    }

    public void setNewScale(byte newScale) {
        this._newScale = newScale;
    }

    public byte getNewScale() {
        return this._newScale;
    }

    public int getPreviousEnemy() {
        return this._previousEnemy;
    }

    public Enemy getJogressPartner() {
        return this._jogressPartner;
    }

    public void setJogressPartner(Enemy e) {
        this._jogressPartner = e;
    }

    public void setKeyboard(KeyboardCursor k) {
        this._keyboard = k;
    }

    public ArrayList<Shell> getShells() {
        return this._shells;
    }

    public ClockTic(SpriteAnim view, Controller model, SoundObj sounds, boolean tournament, String modFolder) {
        this._tournamentVersion = tournament;
        this.MOD_FOLDER = modFolder;
        this._view = view;
        this._model = model;
        this._sounds = sounds;
        this._currentMenu = Enum.Menu.Start;
        this._view.AddListener(this, this._model.getDigimon());
        this.setWindowLoc();
        this._newScale = (byte)this._model.getSettings().getGameScale();
        this._model.getDigimon().createWorld();
        this.buildShells(modFolder);
    }

    public void gameLoop() {
        Thread thread = new Thread(new Runnable(){
            long lastLoopTime = System.nanoTime();

            @Override
            public void run() {
                while (ClockTic.this._gameRunning) {
                    int mod;
                    long now = System.nanoTime();
                    long updateLength = now - this.lastLoopTime;
                    this.lastLoopTime = now;
                    double delta = (double)updateLength / 1.6666666E7;
                    ClockTic.this._lastFPSTime += updateLength;
                    ClockTic.this._FPS++;
                    if (ClockTic.this._lastFPSTime >= 1000000000L) {
                        ClockTic.this._lastFPSTime = 0L;
                        ClockTic.this._FPS = 0;
                    }
                    ClockTic.this.runGame(delta);
                    int speed = (int)((double)ClockTic.this._model.getTime().getClockSpeed() * ViewConfig._loopModCoefficient);
                    int n = mod = speed + 1 > ViewConfig._maxLoopMod ? ViewConfig._maxLoopMod : speed + 1;
                    if (mod <= 0) {
                        mod = 1;
                    }
                    int divisor = 1000000 * (Config._enableFastForward ? mod : 1);
                    long sleepTime = (this.lastLoopTime - System.nanoTime() + 16666666L) / (long)divisor;
                    try {
                        Thread.sleep(sleepTime);
                    }
                    catch (Exception exception) {}
                }
            }
        }, "GameLoop");
        Thread backAnim = new Thread(new Runnable(){

            @Override
            public void run() {
                while (ClockTic.this._gameRunning) {
                    if (ClockTic.this._view.getBackgroundAnim().animate(ClockTic.this._currentMenu)) {
                        try {
                            Thread.sleep(100L);
                        }
                        catch (Exception exception) {}
                        continue;
                    }
                    try {
                        Thread.sleep(50L);
                    }
                    catch (Exception exception) {}
                }
            }
        }, "BackgroundAnim");
        Thread weather = new Thread(new Runnable(){

            @Override
            public void run() {
                while (ClockTic.this._gameRunning) {
                    ClockTic.this._view.checkWeather(ClockTic.this._currentMenu, ClockTic.this._model.getDigimon(), ClockTic.this._battle);
                    try {
                        Thread.sleep(100L);
                    }
                    catch (Exception exception) {}
                }
            }
        }, "Precipitate");
        thread.start();
        backAnim.start();
        weather.start();
    }

    public boolean isSystemSecond() {
        return System.nanoTime() - this._lastNanosecond >= 1L;
    }

    public boolean isPlaying() {
        return !this._model.getDigimon().isPaused();
    }

    private void checkSystemSecond(PhysicalState digimon) {
        boolean playing = this.isPlaying();
        if (this._currentMenu != Enum.Menu.Start && this._currentMenu != Enum.Menu.Set_EggClock && this._currentMenu != Enum.Menu.Save_Name && this._currentMenu != Enum.Menu.Load_Name && this._currentMenu != Enum.Menu.SetDifficulty) {
            long secondEquivalent;
            long currentNanosecond = System.nanoTime();
            long nanoDiff = currentNanosecond - this._lastNanosecond;
            if (nanoDiff / (secondEquivalent = this._model.getTime().getSecondEquivalent()) >= 1L) {
                this._model.getTime().setNanoRemainder(this._model.getTime().getNanoRemainder() + nanoDiff % secondEquivalent, playing, this._model.getDigimon());
                Enum.Time oldTime = this._model.getDigimon().checkTime(this._model.getTime().getHours());
                byte oldHour = this._model.getTime().getHours();
                this.processMinLapsePacket(this._model.getTime().setSeconds((byte)(this._model.getTime().getSeconds() + 1), playing, this._model.getDigimon()));
                this._lastNanosecond = currentNanosecond;
                Enum.Time newTime = this._model.getDigimon().checkTime(this._model.getTime().getHours());
                byte newHour = this._model.getTime().getHours();
                if (oldTime != newTime || newTime == Enum.Time.Noon && oldHour != newHour && digimon.isSunset(newTime)) {
                    this._view.getBackgroundAnim().checkBack(digimon, this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle, this._view.getHabitat());
                }
                this.checkTournamentBattle(digimon);
            }
            if ((currentNanosecond - this._lastCallNanosecond) / 1000000000L >= 1L) {
                if (playing) {
                    this._view.checkCall(digimon, this._currentMenu);
                }
                this._lastCallNanosecond = currentNanosecond;
            }
            long timer = (currentNanosecond - this._lastStepNanosecond) / (secondEquivalent / (long)Config._stepSecondCoefficient);
            if (playing && timer >= 1L) {
                this._lastStepNanosecond = currentNanosecond;
                this.step(digimon);
            }
        }
    }

    private void checkTournamentBattle(PhysicalState digimon) {
        if (digimon.getTournament().getActive() && digimon.getTournament().getIsWon() != 0 && digimon.isFullyRecovered() && digimon.getCurrentState() == Enum.State.Idling && this._currentMenu == Enum.Menu.None && this._battle == null) {
            this.onTourneyBattle();
        }
    }

    private void processMinLapsePacket(MinLapsePacket p) {
        if (p != null) {
            PhysicalState digimon = this._model.getDigimon();
            if (p.getFood() != null) {
                this._view.setFoodType(p.getFood());
                digimon.assistantFeed(p.getFood());
            } else if (p.isLightSwitch()) {
                digimon.setStateNoRepeat(Enum.State.Assistant_Lights);
            } else if (p.isCleaned() && digimon.getCurrentState() != Enum.State.Cleaning && !digimon.getAnimQueue().contains((Object)Enum.State.Cleaning)) {
                digimon.setStateNoRepeat(Enum.State.Assistant_Clean);
            }
        }
    }

    private void runGame(double delta) {
        final PhysicalState digimon = this._model.getDigimon();
        this.checkSystemSecond(digimon);
        SwingUtilities.invokeLater(new Runnable(){
            final /* synthetic */ ClockTic this$0;
            {
                this.this$0 = this$0;
            }

            @Override
            public void run() {
                this.this$0.checkDisplay();
                this.this$0._view.updateDebug(digimon);
            }
        });
    }

    private void checkDisplay() {
        if (!this._currentMenu.equals((Object)Enum.Menu.EvolutionTree)) {
            try {
                if (this._view.getMessage() == null) {
                    if (this._lastMenu != this._currentMenu) {
                        this._menuHistory[0] = this._currentMenu;
                        this._menuHistory[1] = this._lastMenu;
                        this._view.resetScreenExceptMenuRect();
                        this._view.checkSystemMenus(this._currentMenu, this._lastMenu, this._model.getDigimon(), this._model.getSettings());
                    }
                    this._lastMenu = this._currentMenu;
                    this._view.checkAnims(this._currentMenu, this._model.getDigimon());
                    this._view.drawMainBackground(this._currentMenu);
                } else {
                    this._view.displayMessage(this._currentMenu, this._lastMenu, this._model.getDigimon(), this._model.getSettings());
                }
            }
            catch (Exception e) {
                CrashEntry.generateEntry(e);
                e.printStackTrace();
            }
        }
    }

    public boolean isCallSound() {
        return this._model.getTime().getSeconds() % 10 == 0;
    }

    private boolean verifyBackground(Zone z, PhysicalState digimon) {
        int back = z.getCurrentLocationBackground();
        if (digimon.getCurrentHabitat().getID() != back) {
            digimon.setCurrentHabitat(back, false);
            return false;
        }
        return true;
    }

    private void step(PhysicalState digimon) {
        Zone zone;
        Enemy enemy = null;
        WorldMap world = digimon.getWorld();
        if (this._currentMenu == Enum.Menu.None && !digimon.getIsHome() && this._battle == null && (zone = world.getCurrentZone()) != null) {
            boolean isTraveling = world.step(zone);
            if (isTraveling) {
                this.verifyBackground(zone, digimon);
                this._view.getBackgroundAnim().checkBack(digimon, this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
            }
            if (this._view.getCurrentAnim() == Enum.State.Idling && digimon.getAnimQueue().isEmpty()) {
                enemy = zone.checkBattle(false);
            }
            if (isTraveling && enemy == null && zone.checkInvestigate()) {
                digimon.setCurrentState(Enum.State.DiscoverCall);
            }
        }
        this.checkWildEncounter(enemy, world, digimon);
    }

    public void onInvestigate() {
        PhysicalState digimon = this._model.getDigimon();
        WorldMap world = digimon.getWorld();
        Zone zone = world.getCurrentZone();
        if (zone != null) {
            int[] item = zone.checkItem();
            if (item != null) {
                digimon.setGift(item);
                this._model.getDigimon().setCurrentState(Enum.State.Discovering);
            } else {
                digimon.setBattleImmunity(false);
                this._model.getDigimon().setCurrentState(Enum.State.DiscoverEnemy);
            }
        }
    }

    public void onDiscoverItem() {
        this._model.getDigimon().setCurrentState(Enum.State.ReturnItem);
    }

    public void onDiscoverEnemy() {
        PhysicalState digimon = this._model.getDigimon();
        Enemy enemy = null;
        WorldMap world = digimon.getWorld();
        Zone zone = world.getCurrentZone();
        while (enemy == null) {
            enemy = zone.checkBattle(true);
        }
        this.checkWildEncounter(enemy, world, digimon);
    }

    public WorldMap onTravel() {
        PhysicalState digimon = this._model.getDigimon();
        WorldMap world = digimon.getWorld();
        world.setTravelSpeed((byte)(world.getTravelSpeed() + 1));
        return world;
    }

    private void checkWildEncounter(Enemy enemy, WorldMap world, PhysicalState digimon) {
        if (this.checkBattleWait(world) && digimon.getAlive() && enemy != null && this.battleStart(Battle.BattleType.PvE_Wild, enemy)) {
            digimon.disturb(Config._rankChangeDisturb);
            world.isWildEncounter();
            this._battle.addToBattleRecord(this.getBattleInfo(digimon));
            digimon.setCurrentState(Enum.State.Battle_Flash);
        }
    }

    private boolean checkBattleWait(WorldMap world) {
        if (world.battleWait(this._battle)) {
            this._battle.escape();
            this._view.getBattleFlash().removeIcon();
            this._view.getBattleFlash().setVisible(false);
            this._view.disposeMusic();
            this._view.endAnim();
            this._view.drawMainMenu();
            this._currentMenu = Enum.Menu.None;
            this.resetBattle();
            this.verifyBackground(world.getCurrentZone(), this._model.getDigimon());
            this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
            return false;
        }
        return true;
    }

    public void onTourneyBattle() {
        PhysicalState digimon = this.getModel().getDigimon();
        this.setupTourneyBattle(digimon);
        digimon.setCurrentState(Enum.State.Battle_Flash);
    }

    private void setupTourneyBattle(PhysicalState digimon) {
        if (this.battleStart(Battle.BattleType.PvE_Tourney, digimon.getTournament().getCurrentEnemy())) {
            this._battle.addToBattleRecord(this.getBattleInfo(digimon));
        }
    }

    public void giftEnd() {
        PhysicalState digimon = this._model.getDigimon();
        int[] g = digimon.getGift();
        if (g != null && g[1] == 0) {
            digimon.getItemByID(digimon.getGift()[0]).incQuantity();
        } else if (g != null && g[1] == 1) {
            digimon.getFoodByID(digimon.getGift()[0]).incQuantity();
        }
        Enum.State newState = Enum.State.Idling;
        if (this._view.getCurrentAnim() == Enum.State.ReturnItem) {
            digimon.setPraise(true);
        } else {
            newState = Enum.State.Cheering;
        }
        this._view.resetScreen();
        this._view.endAnim();
        digimon.setCurrentState(newState);
    }

    public void attentionFail(Enum.State state) {
        switch (state) {
            default: 
        }
    }

    private void buildShells(String modFolder) {
        try (InputStream in = Utility.getInputStream(modFolder + "csv" + File.separator, "/View/", "shellConfig.csv");
             BufferedReader reader = new BufferedReader(new InputStreamReader(in, "utf-8"));){
            String line = reader.readLine();
            while ((line = reader.readLine()) != null) {
                this._shells.add(new Shell(line.split(",")));
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    public boolean setIdleType() {
        boolean isUnwell = false;
        PhysicalState myDigimon = this._model.getDigimon();
        if (myDigimon.isSick() || myDigimon.isInj() || myDigimon.getCurrentMood() == Enum.Mood.Depressed || myDigimon.getWorld().getTravelSpeed() > 0 && (myDigimon.getEnergy() <= 0 || myDigimon.isFatigued())) {
            isUnwell = true;
        }
        return isUnwell;
    }

    public void canJogress() {
        this._view.setJogressMatch(this._model.getDigimon().canJogress());
        if (!this._view.getJogressMatch().equals("")) {
            this._sounds.playSound(SoundConfig._click);
            this.onMultiOption();
        } else {
            this.setCurrentMenu(Enum.Menu.None);
        }
    }

    public void onStatus(MouseEvent e) {
        switch (this._currentMenu) {
            case None: {
                this._currentMenu = Enum.Menu.Data_Status;
                break;
            }
            default: {
                this._currentMenu = Enum.Menu.None;
                this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
            }
        }
    }

    public void reverseDataMenu() {
        if (this._currentMenu != Enum.Menu.None) {
            switch (this._currentMenu) {
                case Data_Status: {
                    this._currentMenu = Enum.Menu.Data_Clock;
                    break;
                }
                case Data_Hunger: {
                    this._currentMenu = Enum.Menu.Data_Status;
                    break;
                }
                case Data_Strength: {
                    this._currentMenu = Enum.Menu.Data_Hunger;
                    break;
                }
                case Data_Energy: {
                    this._currentMenu = Enum.Menu.Data_Strength;
                    break;
                }
                case Data_HP: {
                    this._currentMenu = Enum.Menu.Data_Energy;
                    break;
                }
                case Data_Power: {
                    this._currentMenu = Enum.Menu.Data_HP;
                    break;
                }
                case Data_Battles: {
                    this._currentMenu = Enum.Menu.Data_Power;
                    break;
                }
                case Data_Person: {
                    this._currentMenu = Enum.Menu.Data_Battles;
                    break;
                }
                case Data_Clock: {
                    this._currentMenu = Enum.Menu.Data_Person;
                }
            }
        }
    }

    public void onPerson() {
        this._currentMenu = Enum.Menu.Data_Person_Detail;
    }

    public void onMenu(MouseEvent e) {
        if (SwingUtilities.isRightMouseButton(e)) {
            this.reverseDataMenu();
        } else {
            switch (this._currentMenu) {
                case MapZoneSelect: {
                    PhysicalState digimon = this._model.getDigimon();
                    this._currentMenu = Enum.Menu.None;
                    if (!digimon.canTeleport()) break;
                    digimon.setBattleImmunity(true);
                    digimon.setCurrentState(Enum.State.Teleport_Leave);
                    break;
                }
                case None: {
                    switch (this._model.getDigimon().getCurrentState()) {
                        case Eating: 
                        case Munching: 
                        case Bandaging: 
                        case Assistant_Feed: {
                            this._view.resetScreen();
                            this._view.endAnim();
                            break;
                        }
                        case BossParade: {
                            this._view.disposeMusic();
                            this._view.resetScreen();
                            this._view.endAnim();
                            this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
                        }
                    }
                    break;
                }
                case Jogress_Mismatch: {
                    this._currentMenu = Enum.Menu.Battle_Validation;
                    this.canJogress();
                    break;
                }
                case ConnectError_Jogress: {
                    this._currentMenu = Enum.Menu.Multi_Validation_Jogress;
                    break;
                }
                case ConnectError_Battle: {
                    this._currentMenu = Enum.Menu.Multi_Validation_Battle;
                    break;
                }
                case Data_Status: {
                    this._currentMenu = Enum.Menu.Data_Hunger;
                    break;
                }
                case Data_Hunger: {
                    this._currentMenu = Enum.Menu.Data_Strength;
                    break;
                }
                case Data_Strength: {
                    this._currentMenu = Enum.Menu.Data_Energy;
                    break;
                }
                case Data_Energy: {
                    this._currentMenu = Enum.Menu.Data_HP;
                    break;
                }
                case Data_HP: {
                    this._currentMenu = Enum.Menu.Data_Power;
                    break;
                }
                case Data_Power: {
                    this._currentMenu = Enum.Menu.Data_Battles;
                    break;
                }
                case Data_Battles: {
                    this._currentMenu = Enum.Menu.Data_Person;
                    break;
                }
                case Data_Person: {
                    this._currentMenu = Enum.Menu.Data_Clock;
                    break;
                }
                case Data_Clock: {
                    this._currentMenu = Enum.Menu.Data_Status;
                }
            }
        }
    }

    public void onClose() {
        switch (this._currentMenu) {
            case Start: {
                this._view.dispose();
                System.exit(0);
                break;
            }
            case Settings: {
                boolean rescale;
                boolean bl = rescale = (double)this._newScale != this._model.getSettings().getGameScale();
                if (rescale) {
                    this.setWindowLoc();
                    this._view.setVisible(false);
                    this._view.dispose();
                    this._model.getSettings().setGameScale(this._newScale);
                    this._view.restartView(this._newScale, this._model.getSettings().getShell(), this._model.getSettings().isSound(), this._model.getSettings().isOnTop());
                    this._view.AddListener(this, this._model.getDigimon());
                    this._view.freeStartMenuResources();
                    this._currentMenu = Enum.Menu.Loading;
                    this._view.resetScreen();
                    this._view.setVisible(true);
                    this._view.setIsLoaded(true);
                    this._view.getCharacter().setVisible(false);
                    this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
                }
                this._view.setupShell(this.getCurrentShell());
                if (rescale) {
                    ViewUtil.centerMain(this._view);
                }
                this._currentMenu = Enum.Menu.None;
                break;
            }
            case EvolutionTree: {
                try {
                    if (this._tree != null) {
                        this._tree.dispose();
                        this._tree = null;
                    }
                    this._view.setVisible(true);
                    this._view.requestFocus();
                    this._lastMenu = Enum.Menu.EvolutionTree;
                    this._currentMenu = Enum.Menu.None;
                }
                catch (IllegalComponentStateException e) {
                    CrashEntry.generateEntry("IllegalComponentStateException in onClose method, EvolutionTree enum - What the heck");
                    this._view.setVisible(true);
                    this._view.requestFocus();
                }
                catch (Exception e) {
                    CrashEntry.generateEntry(e);
                }
                break;
            }
            case Set_EggClock: {
                this._view.requestFocus();
                this._currentMenu = Enum.Menu.Start;
                break;
            }
            case SetDifficulty: {
                this._view.requestFocus();
                this._currentMenu = Enum.Menu.Set_EggClock;
                break;
            }
            case Save_Name: {
                this._view.requestFocus();
                this._currentMenu = Enum.Menu.SetDifficulty;
                break;
            }
            case Load_Name: {
                this._view.requestFocus();
                this._currentMenu = Enum.Menu.Start;
                break;
            }
            case Host_Name_Battle: 
            case Host_Port_Battle: {
                this._currentMenu = Enum.Menu.Multi_Validation_Battle;
                this._view.drawMainBackground(this._currentMenu);
                this._view.drawMainMenu();
                this._view.requestFocus();
                break;
            }
            case Host_Name_Jogress: 
            case Host_Port_Jogress: {
                this._currentMenu = Enum.Menu.Multi_Validation_Jogress;
                this._view.drawMainBackground(this._currentMenu);
                this._view.drawMainMenu();
                this._view.requestFocus();
            }
        }
        if (this._currentMenu == Enum.Menu.None) {
            this._view.setFrame(0);
        }
    }

    public Enum.Field getDNARate(int rate) {
        Enum.Field f = Enum.Field.NA;
        f = rate <= Config._noneRateMax ? Enum.Field.None : (rate <= Config._deepSaverRateMax ? Enum.Field.DeepSaver : (rate <= Config._jungleTrooperRateMax ? Enum.Field.JungleTrooper : (rate <= Config._natureSpiritRateMax ? Enum.Field.NatureSpirit : (rate <= Config._windGuardianRateMax ? Enum.Field.WindGuardian : (rate <= Config._dragonsRoarRateMax ? Enum.Field.DragonsRoar : (rate <= Config._metalEmpireRateMax ? Enum.Field.MetalEmpire : (rate <= Config._nightmareSoldierRateMax ? Enum.Field.NightmareSoldier : (rate <= Config._virusBusterRateMax ? Enum.Field.VirusBuster : (rate <= Config._darkAreaRateMax ? Enum.Field.DarkArea : Enum.Field.None)))))))));
        return f;
    }

    public void onDNAGenerate(int rate) {
        Enum.Field f = this.getDNARate(rate);
        if (f != Enum.Field.NA) {
            PhysicalState digimon = this._model.getDigimon();
            int amount = this._view.getDNAAmount();
            DNA dna = this._model.getDigimon().getDNA();
            int owned = dna.getOwned(f);
            if (owned + amount > Config._maxDNAInventory) {
                digimon.setBits(digimon.getBits() + (owned + amount - Config._maxDNAInventory));
            }
            dna.generateDNA(f, amount);
            digimon.setUnlockConsumable(f.ordinal());
            digimon.setCurrentState(Enum.State.UnlockDNA);
        } else {
            this._model.getDigimon().setCurrentState(Enum.State.Jeering);
        }
        this._numHits = 0;
        this._currentMenu = Enum.Menu.None;
    }

    public boolean onEnter() {
        boolean sound = true;
        boolean exists = true;
        PhysicalState digimon = this._model.getDigimon();
        switch (this._currentMenu) {
            case TrophyPrizeBits: {
                this._currentMenu = Enum.Menu.TrophyPrizeItem;
                break;
            }
            case DNA_Detail: {
                digimon.applyDNA(Enum.Field.values()[this._view.getConsumablePage()], this._view.getDNAAmount());
                this._currentMenu = Enum.Menu.None;
                break;
            }
            case DNA_GenerateValidate: {
                int amount = this._view.getDNAAmount();
                this._currentMenu = Enum.Menu.None;
                if (this._model.getDigimon().getBits() >= amount) {
                    this._model.getDigimon().setBits(this._model.getDigimon().getBits() - amount);
                    this._model.getDigimon().setPriorityState(Enum.State.DNA_Generate);
                    this._view.setFrame(-1);
                    break;
                }
                this._model.getDigimon().setCurrentState(Enum.State.Jeering);
                break;
            }
            case Habitat_Shop_Description: {
                if (this._view.getHabitat() < 0 || this._view.getHabitat() >= this._model.getDigimon().getHabitats().size()) break;
                this._currentMenu = Enum.Menu.Habitat_Shop_Compatibility;
                this._view.setConsumablePage(this._view.getCurrentFieldElement(this._currentMenu));
                break;
            }
            case Habitat_Shop_Compatibility: {
                if (this._view.getHabitat() < 0 || this._view.getHabitat() >= this._model.getDigimon().getHabitats().size()) break;
                this._currentMenu = Enum.Menu.Habitat_Shop_Incompatibility;
                this._view.setConsumablePage(this._view.getCurrentFieldElement(this._currentMenu));
                break;
            }
            case Habitat_Shop_Incompatibility: {
                if (this._view.getHabitat() < 0 || this._view.getHabitat() >= this._model.getDigimon().getHabitats().size()) break;
                this._currentMenu = Enum.Menu.Habitat_Purchase;
                this._view.getBackgroundAnim().checkBackNoAnim(digimon, this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle, this._view.getHabitat());
                break;
            }
            case Habitat_Shop: {
                this._currentMenu = Enum.Menu.Habitat_Shop_Description;
                break;
            }
            case Habitat_Inventory: {
                this._currentMenu = Enum.Menu.Habitat_Description;
                break;
            }
            case Habitat_Description: {
                this._currentMenu = Enum.Menu.Habitat_Compatibility;
                this._view.setConsumablePage(this._view.getCurrentFieldElement(this._currentMenu));
                break;
            }
            case Habitat_Compatibility: {
                this._currentMenu = Enum.Menu.Habitat_Incompatibility;
                this._view.setConsumablePage(this._view.getCurrentFieldElement(this._currentMenu));
                break;
            }
            case ZoneDetail: {
                this._currentMenu = Enum.Menu.Steps;
                break;
            }
            case Food_Sale: {
                this._view.endAnim();
                this._currentMenu = Enum.Menu.None;
                digimon.setCurrentState(Enum.State.Selling_Food);
                break;
            }
            case Item_Sale: {
                this._view.endAnim();
                this._currentMenu = Enum.Menu.None;
                digimon.setCurrentState(Enum.State.Selling_Item);
                break;
            }
            case Food_Purchase: {
                if (this.canBuy(this._view.getFoodType(), this._view.getConsumableType())) {
                    this._view.endAnim();
                    this._currentMenu = Enum.Menu.None;
                    digimon.setCurrentState(Enum.State.Buying_Food);
                    break;
                }
                sound = false;
                this._sounds.playSound(SoundConfig._error);
                break;
            }
            case Item_Purchase: {
                if (this.canBuy(this._view.getItemType(), this._view.getConsumableType())) {
                    this._view.getItemType();
                    this._view.endAnim();
                    this._currentMenu = Enum.Menu.None;
                    digimon.setCurrentState(Enum.State.Buying_Item);
                    break;
                }
                sound = false;
                this._sounds.playSound(SoundConfig._error);
                break;
            }
            case Habitat_Purchase: {
                this._view.endAnim();
                this._currentMenu = Enum.Menu.None;
                digimon.setCurrentState(Enum.State.Buying_Habitat);
                break;
            }
            case Tourney_Registration: {
                if (!digimon.getTournament().checkTourneyClosed(this._model.getDigimon().getTournament().getTourneyTime(this._view.getTrophyInSchedule()), this._model.getTime().getHours()) && this._model.getDigimon().getTournament().isEligible()) {
                    this._currentMenu = Enum.Menu.Tourney_Validation;
                    break;
                }
                digimon.setCurrentState(Enum.State.Jeering);
                this._currentMenu = Enum.Menu.None;
                break;
            }
            case Royale_Lineup: {
                this._currentMenu = Enum.Menu.Roster;
                break;
            }
            case Roster: {
                this._currentMenu = Enum.Menu.Tourney_Surrender;
                break;
            }
            case Set_EggClock: {
                this._currentMenu = Enum.Menu.SetDifficulty;
                break;
            }
            case Save_Name: {
                String saveString = this._view.getStringPane().getText().trim();
                try {
                    String savePath = "files" + File.separator + "saves" + File.separator + saveString + ".txt";
                    File saveFile = new File(savePath);
                    exists = saveFile.exists();
                    if (saveString.trim().length() > 0 && !this.containsIllegalChar(saveString) && !exists) {
                        Config.loadConfig(digimon.getDifficultySetting(), this.MOD_FOLDER, this._tournamentVersion);
                        digimon.initConfigVariables();
                        this.setTimeFromString();
                        digimon.setDigimon(digimon.getEvolution().getStartingDigimon().get(this._view.getConsumablePage()), false);
                        digimon.getWorld().startMap(Config._startingMap);
                        this._view.setupZones();
                        digimon.setChecksum(Checksum.generate());
                        digimon.loadTree();
                        if (!saveFile.getParentFile().exists()) {
                            saveFile.getParentFile().mkdirs();
                        }
                        if (!saveFile.exists()) {
                            saveFile.createNewFile();
                        }
                        PrintWriter p = new PrintWriter(saveFile);
                        p.close();
                        digimon.setSaveString(saveString + ".txt");
                        digimon.setBits(Config._startingBits);
                        digimon.getHabitats().get(Config._startingHabitat).setUnlocked(true);
                        digimon.setCurrentHabitat(Config._startingHabitat);
                        digimon.setTrophySchedule();
                        digimon.setDayTemp();
                        digimon.save(false);
                        this._view.getBackgroundAnim().checkBackNoAnim(digimon, this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
                        this._view.getBackgroundAnim().animate(this._currentMenu);
                        this._view.setupShell(this.getCurrentShell());
                        ViewUtil.centerMain(this._view);
                        this.setWindowLoc();
                        this._currentMenu = Enum.Menu.None;
                        this._view.setIsLoaded(true);
                        this._view.disposeMusic();
                        this._lastNanosecond = System.nanoTime();
                        this._view.initStringPane(-1);
                        this._view.freeStartMenuResources();
                        break;
                    }
                    sound = false;
                    this._sounds.playSound(SoundConfig._error);
                    this._view.getStringPane().setText("");
                    this._view.getStringPane().requestFocus();
                    this._keyboard.resetStringPane(this._view.getStringPane());
                }
                catch (Exception e) {
                    CrashEntry.generateEntry(e);
                    e.printStackTrace();
                }
                break;
            }
            case Load_Name: {
                String loadString = this._view.getStringPane().getText().trim();
                File f = new File("files" + File.separator + "saves" + File.separator + loadString + ".txt");
                if (loadString.trim().length() > 0 && f.exists()) {
                    digimon.setSaveString(loadString + ".txt");
                    digimon.checkLoadType();
                    this.loadSettings();
                    this.setWindowLoc();
                    this._view.getBackgroundAnim().checkBackNoAnim(digimon, this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
                    this._view.getBackgroundAnim().animate(this._currentMenu);
                    this._view.setupShell(this.getCurrentShell());
                    ViewUtil.centerMain(this._view);
                    this._currentMenu = Enum.Menu.None;
                    this._view.setIsLoaded(true);
                    this._view.disposeMusic();
                    if (this._model.getDigimon().getWorld().getCurrentMap() == null) {
                        digimon.getWorld().startMap(1);
                    }
                    this._view.setupZones();
                    this._lastNanosecond = System.nanoTime();
                    this._view.initStringPane(-1);
                    this._view.freeStartMenuResources();
                    break;
                }
                sound = false;
                this._sounds.playSound(SoundConfig._error);
                this._view.getStringPane().setText("");
                this._view.getStringPane().requestFocus();
                this._keyboard.resetStringPane(this._view.getStringPane());
                break;
            }
            case Host_Port_Battle: {
                this.onHostBattle();
                this._view.requestFocus();
                break;
            }
            case Host_Port_Jogress: {
                this.onHostJogress();
                this._view.requestFocus();
                break;
            }
            case Host_Name_Jogress: {
                this._currentMenu = Enum.Menu.None;
                this._connectJogress = new JogressConnect(this, this._view.getStringPane().getText().trim(), this._view.getJogressMatch());
                digimon.setCurrentState(Enum.State.Jogress_Flash);
                this._view.drawMainMenu();
                this._view.requestFocus();
                break;
            }
            case Host_Name_Battle: {
                this._currentMenu = Enum.Menu.None;
                if (digimon.canBattle(false)) {
                    this._connectBattle = new BattleConnect(this, this._view.getStringPane().getText().trim());
                }
                this._view.drawMainMenu();
                this._view.requestFocus();
            }
        }
        return sound;
    }

    private boolean canBuy(Consumable c, ShopConsumable s) {
        int i = this._view.getPurchaseAmount();
        return this._model.getDigimon().getBits() >= s.getPurchasePrice() * i && c.canIncQuantity(i);
    }

    private boolean containsIllegalChar(String s) {
        boolean illegalChar = false;
        for (char c : s.toCharArray()) {
            if (Character.isLetter(c)) continue;
            illegalChar = true;
            break;
        }
        return illegalChar;
    }

    public void onJogress() {
        if (this._hostJogress != null && this._hostJogress.getJogressMatch().trim().equals("")) {
            this.onError(false);
        } else if (this._connectJogress != null && !this._connectJogress.getJogressMatch().trim().equals("")) {
            this._connectJogress.checkJogressStart();
        } else {
            this.onError(false);
        }
    }

    public void onBattleFlash() {
        WorldMap world = this._model.getDigimon().getWorld();
        if (this._battle != null && world.getWildBattleWait() && this._battle.getBattleType() == Battle.BattleType.PvE_Wild) {
            this._model.getDigimon().setCurrentState(Enum.State.Battle_Start);
            world.setWildBattleWait(false);
        } else if (this._hostBattle != null && this._hostBattle.getMultiBattle()) {
            this.onError(true);
        } else if (this._connectBattle != null && this._connectBattle.getMultiBattle()) {
            this._connectBattle.checkBattleStart();
        } else if (this._battle != null && this._battle.getBattleType() != Battle.BattleType.PvE_Wild) {
            this._model.getDigimon().setCurrentState(Enum.State.Battle_Start);
        } else {
            this._view.endAnim();
            this._view.resetScreen();
        }
    }

    public void onMismatch() {
        this.endConnection();
        this._view.endAnim();
        this._sounds.playSound(SoundConfig._jogressMismatch);
        this._currentMenu = Enum.Menu.Jogress_Mismatch;
    }

    public void onError(boolean isBattle) {
        this.onConnectionError(isBattle);
        this._view.endAnim();
        this.endConnection();
        this._sounds.playSound(SoundConfig._error);
    }

    public void multiBattleStartConnector(Enemy e, int difficulty) {
        this.multiBattleStart(e, difficulty);
    }

    public void multiBattleStart(Enemy e, int difficulty) {
        if (this.battleStart(Battle.BattleType.PvP, e)) {
            this._battle.setOppDifficulty(difficulty);
            this._view.endAnim();
            this._model.getDigimon().setCurrentState(Enum.State.Battle_Start);
            this._battle.addToBattleRecord(this.getMultiInfo(this._model.getDigimon()));
            this._battle.addToBattleRecord(this.getBattleInfo(this._model.getDigimon()));
        }
    }

    public void startJogress(String jogressMatch, boolean isSick) {
        if (!jogressMatch.equals("")) {
            this._view.setJogressMatch(jogressMatch + "," + this.getJogressIndex());
            this._view.endAnim();
            this._model.getDigimon().setCurrentState(Enum.State.Jogress_Start);
            this.endConnection();
            if (isSick) {
                this._model.getDigimon().checkSick(90);
            }
        } else {
            this.onMismatch();
        }
    }

    private void loadSettings() {
        this._view.setAlwaysOnTop(this._model.getSettings().isOnTop());
        if ((double)this._newScale != this._model.getSettings().getGameScale()) {
            this._currentMenu = Enum.Menu.Loading;
            this._newScale = (byte)this._model.getSettings().getGameScale();
            this._view.dispose();
            this._view.restartView(this._newScale, this._model.getSettings().getShell(), this._model.getSettings().isSound(), this._model.getSettings().isOnTop());
            this._view.AddListener(this, this._model.getDigimon());
            this._currentMenu = Enum.Menu.Loading;
            this._view.setVisible(true);
            this._model.getSettings().setGameScale(this._newScale);
            this._view.getCharacter().setVisible(false);
        }
    }

    public void onCycleUp() {
        switch (this._currentMenu) {
            case EvolutionTree: {
                this._tree.decTreePage();
                break;
            }
            case Settings: {
                this._model.getSettings().setShell(this._view.setShellPage(this._view.getConsumablePage() - 1));
                break;
            }
        }
    }

    public void onCycleDown() {
        switch (this._currentMenu) {
            case EvolutionTree: {
                this._tree.incTreePage();
                break;
            }
            case Settings: {
                this._model.getSettings().setShell(this._view.setShellPage(this._view.getConsumablePage() + 1));
                break;
            }
        }
    }

    public boolean onCycleLeft() {
        boolean b = true;
        PhysicalState digimon = this._model.getDigimon();
        switch (this._currentMenu) {
            case Data_Likes: {
                if (digimon.getFoodIntolerance().size() > 0) {
                    this._currentMenu = Enum.Menu.Data_Intolerant;
                    break;
                }
                this._currentMenu = Enum.Menu.Data_SpeciesDislikes;
                break;
            }
            case Data_Dislikes: {
                this._currentMenu = Enum.Menu.Data_Likes;
                break;
            }
            case Data_SpeciesLikes: {
                this._currentMenu = Enum.Menu.Data_Dislikes;
                break;
            }
            case Data_SpeciesDislikes: {
                this._currentMenu = Enum.Menu.Data_SpeciesLikes;
                break;
            }
            case Data_Intolerant: {
                this._currentMenu = Enum.Menu.Data_SpeciesDislikes;
                break;
            }
            case DNA_Detail: {
                this._view.changeDNAChargeQuantity(false, this._model.getDigimon().getDNA());
                break;
            }
            case DNA_GenerateValidate: {
                this._view.changeDNAQuantity(false, 99);
                break;
            }
            case Food_Purchase: 
            case Item_Purchase: {
                b = this._view.changePurchaseAmount(false, "-");
                break;
            }
            case Food_Sale: 
            case Item_Sale: {
                b = this._view.changePurchaseAmount(false, "+");
                break;
            }
            case EvolutionTree: {
                this._tree.decDuplicatePage();
                break;
            }
            case ZoneDetail: {
                this._model.getDigimon().getWorld().setTravelRight(false);
                break;
            }
            case Habitat_Shop: {
                if (!this._model.getDigimon().lockedHabitatsRemain()) break;
                this._view.setHabitat(this._view.getHabitat() - 1, this._currentMenu == Enum.Menu.Habitat_Shop, true);
                this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle, this._view.getHabitat());
                break;
            }
            case Habitat_Shop_Compatibility: 
            case Habitat_Shop_Incompatibility: 
            case Habitat_Compatibility: 
            case Habitat_Incompatibility: {
                this._view.setHabitatCompatibilityPage(this._view.getConsumablePage() - 1, this._currentMenu);
                break;
            }
            case Habitat_Inventory: {
                this._view.setHabitat(this._view.getHabitat() - 1, this._currentMenu == Enum.Menu.Habitat_Shop, true);
                this._model.getDigimon().setCurrentHabitat(this._view.getHabitat());
                this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
                break;
            }
            case Data_BattleLevels: {
                this._view.setLevelPage(this._view.getConsumablePage() - 1);
                break;
            }
            case DNA_Stats: 
            case DNA_Inventory: {
                this._view.setDNAPage(this._view.getConsumablePage() - 1);
                if (this._currentMenu == Enum.Menu.DNA_Stats) {
                    this._view.drawDNAStats();
                    break;
                }
                this._view.drawDNACharge();
                break;
            }
            case Food_Inventory: {
                b = this._view.setConsumablePage(false, false, this._view.getConsumablePage() - 1, FoodType.class);
                this._view.drawFoodInventory();
                break;
            }
            case Food_Inventory_Sell: {
                b = this._view.setConsumablePage(this._currentMenu, this._view.getConsumablePage() - 1);
                this._view.drawFoodSaleInventory();
                break;
            }
            case Food_Shop: {
                b = this._view.setConsumablePage(true, false, this._view.getConsumablePage() - 1, FoodType.class);
                this._view.drawFoodShop();
                break;
            }
            case Item_Inventory: {
                b = this._view.setConsumablePage(false, false, this._view.getConsumablePage() - 1, Item.class);
                this._view.drawItemInventory();
                break;
            }
            case Item_Inventory_Sell: {
                b = this._view.setConsumablePage(this._currentMenu, this._view.getConsumablePage() - 1);
                this._view.drawItemSaleInventory();
                break;
            }
            case Item_Shop: {
                b = this._view.setConsumablePage(true, false, this._view.getConsumablePage() - 1, Item.class);
                this._view.drawItemShop();
                break;
            }
            case EvolutionInventory: {
                b = this._view.setConsumablePage(false, true, this._view.getConsumablePage() - 1, Item.class);
                this._view.drawEvolutionInventory();
                break;
            }
            case Tourney_Enter: {
                this._view.setTrophyInSchedule(this._view.getTrophyInSchedule() - 1);
                break;
            }
            case WorldMapSelect: {
                this._view.setMapPage(this._view.getConsumablePage() - 1, true);
                break;
            }
            case WorldMapSelect_Ticket: {
                this._view.setMapPage(this._view.getConsumablePage() - 1, false);
                break;
            }
            case Spring_Records: {
                this._view.setTrophyPage(this._view.getTrophyPage() - 1, Enum.Season.Spring);
                this._view.drawRecordsMenu(Enum.Season.Spring);
                break;
            }
            case Summer_Records: {
                this._view.setTrophyPage(this._view.getTrophyPage() - 1, Enum.Season.Summer);
                this._view.drawRecordsMenu(Enum.Season.Summer);
                break;
            }
            case Fall_Records: {
                this._view.setTrophyPage(this._view.getTrophyPage() - 1, Enum.Season.Fall);
                this._view.drawRecordsMenu(Enum.Season.Fall);
                break;
            }
            case Winter_Records: {
                this._view.setTrophyPage(this._view.getTrophyPage() - 1, Enum.Season.Winter);
                this._view.drawRecordsMenu(Enum.Season.Winter);
                break;
            }
            default: {
                this._view.setEggPage(this._view.getConsumablePage() - 1, this._currentMenu);
            }
        }
        return b;
    }

    public boolean onCycleRight() {
        boolean b = true;
        PhysicalState digimon = this._model.getDigimon();
        switch (this._currentMenu) {
            case Data_Likes: {
                this._currentMenu = Enum.Menu.Data_Dislikes;
                break;
            }
            case Data_Dislikes: {
                this._currentMenu = Enum.Menu.Data_SpeciesLikes;
                break;
            }
            case Data_SpeciesLikes: {
                this._currentMenu = Enum.Menu.Data_SpeciesDislikes;
                break;
            }
            case Data_SpeciesDislikes: {
                if (digimon.getFoodIntolerance().size() > 0) {
                    this._currentMenu = Enum.Menu.Data_Intolerant;
                    break;
                }
                this._currentMenu = Enum.Menu.Data_Likes;
                break;
            }
            case Data_Intolerant: {
                this._currentMenu = Enum.Menu.Data_Likes;
                break;
            }
            case DNA_Detail: {
                this._view.changeDNAChargeQuantity(true, this._model.getDigimon().getDNA());
                break;
            }
            case DNA_GenerateValidate: {
                this._view.changeDNAQuantity(true, 99);
                break;
            }
            case Food_Purchase: 
            case Item_Purchase: {
                b = this._view.changePurchaseAmount(true, "-");
                break;
            }
            case Food_Sale: 
            case Item_Sale: {
                b = this._view.changePurchaseAmount(true, "+");
                break;
            }
            case EvolutionTree: {
                this._tree.incDuplicatePage();
                break;
            }
            case Data_BattleLevels: {
                this._view.setLevelPage(this._view.getConsumablePage() + 1);
                break;
            }
            case DNA_Stats: 
            case DNA_Inventory: {
                this._view.setDNAPage(this._view.getConsumablePage() + 1);
                if (this._currentMenu == Enum.Menu.DNA_Stats) {
                    this._view.drawDNAStats();
                    break;
                }
                this._view.drawDNACharge();
                break;
            }
            case Data_Status: {
                this._view.cycleType();
                break;
            }
            case ZoneDetail: {
                this._model.getDigimon().getWorld().setTravelRight(true);
                break;
            }
            case Habitat_Shop: {
                if (!this._model.getDigimon().lockedHabitatsRemain()) break;
                this._view.setHabitat(this._view.getHabitat() + 1, this._currentMenu == Enum.Menu.Habitat_Shop, false);
                this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle, this._view.getHabitat());
                break;
            }
            case Habitat_Inventory: {
                this._view.setHabitat(this._view.getHabitat() + 1, this._currentMenu == Enum.Menu.Habitat_Shop, false);
                this._model.getDigimon().setCurrentHabitat(this._view.getHabitat());
                this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
                break;
            }
            case Habitat_Shop_Compatibility: 
            case Habitat_Shop_Incompatibility: 
            case Habitat_Compatibility: 
            case Habitat_Incompatibility: {
                this._view.setHabitatCompatibilityPage(this._view.getConsumablePage() + 1, this._currentMenu);
                break;
            }
            case Food_Inventory: {
                b = this._view.setConsumablePage(false, false, this._view.getConsumablePage() + 1, FoodType.class);
                this._view.drawFoodInventory();
                break;
            }
            case Food_Inventory_Sell: {
                b = this._view.setConsumablePage(this._currentMenu, this._view.getConsumablePage() + 1);
                this._view.drawFoodSaleInventory();
                break;
            }
            case Food_Shop: {
                b = this._view.setConsumablePage(true, false, this._view.getConsumablePage() + 1, FoodType.class);
                this._view.drawFoodShop();
                break;
            }
            case Item_Inventory: {
                b = this._view.setConsumablePage(false, false, this._view.getConsumablePage() + 1, Item.class);
                this._view.drawItemInventory();
                break;
            }
            case Item_Inventory_Sell: {
                b = this._view.setConsumablePage(this._currentMenu, this._view.getConsumablePage() + 1);
                this._view.drawItemSaleInventory();
                break;
            }
            case Item_Shop: {
                b = this._view.setConsumablePage(true, false, this._view.getConsumablePage() + 1, Item.class);
                this._view.drawItemShop();
                break;
            }
            case EvolutionInventory: {
                b = this._view.setConsumablePage(false, true, this._view.getConsumablePage() + 1, Item.class);
                this._view.drawEvolutionInventory();
                break;
            }
            case Tourney_Enter: {
                this._view.setTrophyInSchedule(this._view.getTrophyInSchedule() + 1);
                break;
            }
            case WorldMapSelect: {
                this._view.setMapPage(this._view.getConsumablePage() + 1, true);
                break;
            }
            case WorldMapSelect_Ticket: {
                this._view.setMapPage(this._view.getConsumablePage() + 1, false);
                break;
            }
            case Spring_Records: {
                this._view.setTrophyPage(this._view.getTrophyPage() + 1, Enum.Season.Spring);
                this._view.drawRecordsMenu(Enum.Season.Spring);
                break;
            }
            case Summer_Records: {
                this._view.setTrophyPage(this._view.getTrophyPage() + 1, Enum.Season.Summer);
                this._view.drawRecordsMenu(Enum.Season.Summer);
                break;
            }
            case Fall_Records: {
                this._view.setTrophyPage(this._view.getTrophyPage() + 1, Enum.Season.Fall);
                this._view.drawRecordsMenu(Enum.Season.Fall);
                break;
            }
            case Winter_Records: {
                this._view.setTrophyPage(this._view.getTrophyPage() + 1, Enum.Season.Winter);
                this._view.drawRecordsMenu(Enum.Season.Winter);
                break;
            }
            default: {
                this._view.setEggPage(this._view.getConsumablePage() + 1, this._currentMenu);
            }
        }
        return b;
    }

    public void onLeftComma() {
        PhysicalState digimon = this._model.getDigimon();
        for (int tenMinutes = 600; tenMinutes > 0; --tenMinutes) {
            digimon.setLapsedLife(digimon.getLapsedLife() - 1L);
        }
        for (int i = 10; i > 0; --i) {
            byte currentMin = this._model.getTime().getMinutes();
            this.onMinusMinutes();
            byte newMin = this._model.getTime().getMinutes();
            if (digimon.getTimeToAge() == 0 && digimon.getAge() > 0) {
                digimon.setTimeToAge(1439);
                digimon.setAge(digimon.getAge() - 1);
            } else {
                digimon.setTimeToAge(digimon.getTimeToAge() - 1);
            }
            if (newMin <= currentMin) continue;
            this.onMinusHours();
        }
        if (digimon.getLapsedLife() < digimon.getTotalLifespan()) {
            digimon.setAlive(true);
        }
    }

    public void onRightPeriod() {
        for (int tenMinutes = 600; tenMinutes > 0; --tenMinutes) {
            this._model.getTime().setSeconds((byte)(this._model.getTime().getSeconds() + 1), this.isPlaying(), this._model.getDigimon());
        }
    }

    public void slowClock() {
        if (Config._enableFastForward) {
            this._model.getTime().setFastMod(1);
        }
    }

    public void onFastClock(int mod) {
        this._model.getTime().setFastMod(mod, true);
        this._model.getTime().setCanResetClockSpeed(false);
    }

    public void onPlusMinutes() {
        byte minutes = (byte)(this._model.getTime().getMinutes() + 1);
        if (minutes == Config._minutesHour) {
            minutes = 0;
        }
        this._model.getTime().setRawSeconds((byte)0);
        this._model.getTime().setNanoRemainder(0L, this.isPlaying(), this._model.getDigimon());
        this._model.getTime().setMinutes(minutes, this._model.getDigimon());
    }

    public void onPlusHours() {
        byte hours = (byte)(this._model.getTime().getHours() + 1);
        if (hours == Config._hoursDay) {
            hours = 0;
        }
        this._model.getTime().setRawSeconds((byte)0);
        this._model.getTime().setNanoRemainder(0L, this.isPlaying(), this._model.getDigimon());
        this._model.getTime().setHours(hours, this._model.getDigimon());
    }

    public void onMinusHours() {
        byte hours = (byte)(this._model.getTime().getHours() - 1);
        this._model.getTime().setRawSeconds((byte)0);
        this._model.getTime().setNanoRemainder(0L, this.isPlaying(), this._model.getDigimon());
        this._model.getTime().setHours(hours, this._model.getDigimon());
    }

    public void onMinusMinutes() {
        byte minutes = (byte)(this._model.getTime().getMinutes() - 1);
        this._model.getTime().setRawSeconds((byte)0);
        this._model.getTime().setNanoRemainder(0L, this.isPlaying(), this._model.getDigimon());
        this._model.getTime().setMinutes(minutes, this._model.getDigimon());
    }

    public void onNewGame() {
        this._currentMenu = Enum.Menu.Set_EggClock;
    }

    public void onLoadButton() {
        this._currentMenu = Enum.Menu.Load_Name;
    }

    public void onDigicore() {
        this._model.getDigimon().forceState(Enum.State.EvolSilhouetteTransition);
        this._currentMenu = Enum.Menu.None;
    }

    public void onFeed(FoodType feedType) {
        this._model.getDigimon().feed(feedType);
        this._currentMenu = Enum.Menu.None;
    }

    public boolean onItemUse(Item item) {
        this._view.endAnim();
        boolean success = true;
        switch (item.getAnim()) {
            case BirdraTransport: 
            case GarudaTransport: {
                if (!this._model.getDigimon().getIsHome()) {
                    this._model.getDigimon().useItem(item);
                    this._currentMenu = Enum.Menu.None;
                    break;
                }
                success = false;
                this._sounds.playSound(SoundConfig._error);
                break;
            }
            case PhoenixTransport: {
                if (!this._model.getDigimon().getIsHome() && this._model.getDigimon().getWorld().getCurrentMap().getTravelZones().length > 0) {
                    this._currentMenu = Enum.Menu.ChooseZone;
                    break;
                }
                success = false;
                this._sounds.playSound(SoundConfig._error);
                break;
            }
            case WhaTransport: {
                if (!this._model.getDigimon().getIsHome() && this._model.getDigimon().getWorld().getTravelMaps().length > 0) {
                    this._currentMenu = Enum.Menu.WorldMapSelect_Ticket;
                    break;
                }
                success = false;
                this._sounds.playSound(SoundConfig._error);
                break;
            }
            case ItemEvol: {
                this._model.getDigimon().useItem(item);
                this._currentMenu = Enum.Menu.None;
                break;
            }
            default: {
                this._view.setItemType(this._model.getDigimon().useItem(item));
                this._currentMenu = Enum.Menu.None;
            }
        }
        return success;
    }

    public void onFeedMenu() {
        if (this._model.getDigimon().getCurrentState() == Enum.State.Eating || this._model.getDigimon().getCurrentState() == Enum.State.Munching) {
            this._view.resetScreen();
            this._view.endAnim();
        }
        if (this._currentMenu != Enum.Menu.None) {
            this._currentMenu = Enum.Menu.None;
            this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
        } else {
            this._currentMenu = Enum.Menu.Feed_Validation;
        }
    }

    public void onInventory() {
        switch (this._currentMenu) {
            case Feed_Validation: {
                this._view.setConsumablePage(false, false, 0, FoodType.class);
                this._currentMenu = Enum.Menu.Food_Inventory;
                break;
            }
            case PraiseScold_Validation: {
                this._currentMenu = Enum.Menu.Inventory_Validation;
            }
        }
    }

    public void onUseFood() {
        this._currentMenu = Enum.Menu.Use_Food;
    }

    public void onUseItem() {
        this._currentMenu = Enum.Menu.Use_Item;
    }

    public void onUseMedFood() {
        this._currentMenu = Enum.Menu.Use_Med_Food;
    }

    public void onUseMedItem() {
        this._currentMenu = Enum.Menu.Use_Med_Item;
    }

    public void onUseEvolutionItem() {
        this._currentMenu = Enum.Menu.UseEvolutionItem;
    }

    public void onShop() {
        PhysicalState digimon = this._model.getDigimon();
        switch (this._currentMenu) {
            case Feed_Validation: {
                if (digimon.getCanSell(true)) {
                    this._currentMenu = Enum.Menu.Food_Buy_Sell_Validation;
                    break;
                }
                this._currentMenu = Enum.Menu.Food_Shop;
                break;
            }
            case PraiseScold_Validation: {
                this._currentMenu = Enum.Menu.Shop_Validation;
            }
        }
        this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
    }

    public void onSellFood() {
        this._currentMenu = Enum.Menu.Sell_Food;
    }

    public void onSellItem() {
        this._currentMenu = Enum.Menu.Sell_Item;
    }

    public void onBuyFood() {
        this._currentMenu = Enum.Menu.Buy_Food;
    }

    public void onBuyItem() {
        this._currentMenu = Enum.Menu.Buy_Item;
    }

    public void onFoodPurchase() {
        this._currentMenu = Enum.Menu.Food_Purchase;
    }

    public void onFoodSale() {
        this._currentMenu = Enum.Menu.Food_Sale;
    }

    public void onItemPurchase() {
        this._currentMenu = Enum.Menu.Item_Purchase;
    }

    public void onItemSale() {
        this._currentMenu = Enum.Menu.Item_Sale;
    }

    public void onDifficulty(int d) {
        this._model.getDigimon().setDifficultySetting(d);
        this._currentMenu = Enum.Menu.Save_Name;
    }

    public void onCharacter() {
        switch (this.getCurrentState()) {
            case Dying: {
                ++this._numHits;
                break;
            }
            case GiftCall: {
                this._view.endAnim();
                this._view.setMessage("Your Digimon wants to give you something");
                this._model.getDigimon().setCurrentState(Enum.State.Gifting);
                break;
            }
            case TournamentAlert: {
                this._view.endAnim();
                this._view.setMessage("ALERT<br>Tournament Open");
                break;
            }
            case DiscoverCall: {
                this._view.endAnim();
                this._view.setMessage("Your Digimon found something");
                this._currentMenu = Enum.Menu.Investigate_Validation;
                break;
            }
            case RequestCall: {
                this._view.endAnim();
                this._view.setMessage(this._model.getDigimon().getRequestMessage());
                this._model.getDigimon().setCurrentState(Enum.State.Requesting);
                break;
            }
            default: {
                this._currentMenu = Enum.Menu.PraiseScold_Validation;
            }
        }
    }

    public void onOpponent() {
        this._currentMenu = Enum.Menu.Enemy_Attacks;
    }

    public void onDescription(boolean isPlayer) {
        this._currentMenu = isPlayer ? Enum.Menu.Attack_Description : Enum.Menu.EnemyAttack_Description;
    }

    public void onPraise() {
        if (!this._model.getDigimon().getAlive()) {
            this._numHits = 0;
            this._currentMenu = Enum.Menu.Restart;
        } else {
            this._currentMenu = Enum.Menu.None;
            this._model.getDigimon().praise();
        }
    }

    public void onScold() {
        this._currentMenu = Enum.Menu.None;
        this._model.getDigimon().scold();
    }

    public void onVitamin(FoodType f) {
        this._currentMenu = Enum.Menu.None;
        this._view.endAnim();
        this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
        this._model.getDigimon().feedVitamin(f);
    }

    public void onFirstAid() {
        switch (this._currentMenu) {
            case Medical: 
            case Use_Med_Food: 
            case Use_Med_Item: 
            case Med_Nutrition: {
                this._currentMenu = Enum.Menu.None;
                this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
                break;
            }
            default: {
                this._currentMenu = Enum.Menu.Medical;
            }
        }
    }

    public void onMed(FoodType f) {
        this._model.getDigimon().feedMed(f);
        this._currentMenu = Enum.Menu.None;
        this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
    }

    public void onBandage(Item i) {
        this._model.getDigimon().applyBandage(i);
        this._currentMenu = Enum.Menu.None;
        this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
    }

    public void onClean() {
        this._model.getDigimon().clean();
    }

    public void onCleanFinish() {
        this._model.getDigimon().clearFilth();
    }

    public boolean onLights() {
        this._model.getDigimon().lightSwitch();
        return this._model.getDigimon().getLights();
    }

    public void onGameButton() {
        this._currentMenu = this._currentMenu != Enum.Menu.None ? Enum.Menu.None : Enum.Menu.Training_Select;
    }

    public void onBattle() {
        this._currentMenu = this._currentMenu != Enum.Menu.None ? Enum.Menu.None : (!this._model.getDigimon().getTournament().getActive() ? Enum.Menu.Battle_Validation : Enum.Menu.Royale_Lineup);
    }

    private boolean battleStart(Battle.BattleType battleType, Enemy e) {
        if (e != null) {
            this._model.getDigimon().setCanEvolveOrDie(false);
            this._battle = new Battle(this._model.getDigimon(), battleType, e);
        }
        return e != null;
    }

    public boolean onMultiOption() {
        boolean valid = true;
        switch (this._currentMenu) {
            case Food_Buy_Sell_Validation: {
                if (!this._model.getDigimon().getSellableFood().isEmpty()) {
                    this._view.setConsumablePage(this._currentMenu, 0);
                    this._currentMenu = Enum.Menu.Food_Inventory_Sell;
                    break;
                }
                valid = false;
                break;
            }
            case Item_Buy_Sell_Validation: {
                if (!this._model.getDigimon().getSellableItems().isEmpty()) {
                    this._view.setConsumablePage(this._currentMenu, 0);
                    this._currentMenu = Enum.Menu.Item_Inventory_Sell;
                    break;
                }
                valid = false;
                break;
            }
            case Battle_VS: {
                if (!this._model.getDigimon().isPaused() && this._model.getDigimon().getGrowthStage() != Enum.Stage.Egg) {
                    this._currentMenu = Enum.Menu.Multi_Validation_Battle;
                    break;
                }
                valid = false;
                break;
            }
            case Battle_Validation: {
                if (!this._model.getDigimon().isPaused() && this._model.getDigimon().getGrowthStage() != Enum.Stage.Egg) {
                    this._currentMenu = Enum.Menu.Multi_Validation_Jogress;
                    break;
                }
                valid = false;
                break;
            }
            case DNA_Validation: {
                if (!this._model.getDigimon().isPaused()) {
                    this._currentMenu = Enum.Menu.DNA_GenerateValidate;
                    break;
                }
                valid = false;
                break;
            }
            case EvolutionMenu: {
                this._currentMenu = Enum.Menu.EvolutionState;
                this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
            }
        }
        return valid;
    }

    private int getJogressIndex() {
        if (this._hostJogress != null) {
            return this._hostJogress.getPartnerIndex();
        }
        if (this._connectJogress != null) {
            return this._connectJogress.getPartnerIndex();
        }
        return -1;
    }

    public void onHost() {
        switch (this._currentMenu) {
            case Multi_Validation_Jogress: {
                this._currentMenu = Enum.Menu.Host_Port_Jogress;
                break;
            }
            case Multi_Validation_Battle: {
                this._currentMenu = Enum.Menu.Host_Port_Battle;
            }
        }
    }

    private void onHostJogress() {
        PhysicalState digimon = this._model.getDigimon();
        this._currentMenu = Enum.Menu.None;
        this._hostJogress = new JogressHost(this, this._view.getJogressMatch(), this._view.getStringPane().getText());
        digimon.setCurrentState(Enum.State.Jogress_Flash);
    }

    private void onHostBattle() {
        PhysicalState digimon = this._model.getDigimon();
        this._currentMenu = Enum.Menu.None;
        if (digimon.canBattle(false)) {
            this._hostBattle = new BattleHost(this, this._view.getStringPane().getText());
        }
    }

    public void onConnect() {
        switch (this._currentMenu) {
            case Multi_Validation_Jogress: {
                this.onConnectJogress();
                break;
            }
            case Multi_Validation_Battle: {
                this.onConnectBattle();
            }
        }
    }

    private void onConnectBattle() {
        this._currentMenu = Enum.Menu.Host_Name_Battle;
    }

    private void onConnectJogress() {
        this._currentMenu = Enum.Menu.Host_Name_Jogress;
    }

    public void onConnectionError(boolean isBattle) {
        if (this._connectBattle != null) {
            this._turnWait = false;
        }
        if (this._hostBattle != null) {
            this._view.disposeMusic();
            this._turnWait = false;
        }
        if (this._battle != null) {
            this.recordBattle("Connection Error");
            this.resetBattle();
        }
        this._currentMenu = isBattle ? Enum.Menu.ConnectError_Battle : Enum.Menu.ConnectError_Jogress;
    }

    public void onDigisoul() {
        if (this._currentMenu == Enum.Menu.None) {
            this._currentMenu = Enum.Menu.EvolutionMenu;
        } else {
            this._currentMenu = Enum.Menu.None;
            this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
        }
    }

    public void onFieldCharge() {
        this._currentMenu = Enum.Menu.DNA_Detail;
    }

    public void onVS() {
        switch (this._currentMenu) {
            case Battle_Validation: {
                this._currentMenu = Enum.Menu.Battle_VS;
                break;
            }
            case DNA_Validation: {
                this._currentMenu = Enum.Menu.DNA_Stats;
                break;
            }
            case EvolutionMenu: {
                this._currentMenu = Enum.Menu.DNA_Validation;
            }
        }
    }

    public void onBattleOptions() {
        this._currentMenu = Enum.Menu.Battle_Style;
    }

    public void onModeChange() {
        this._model.getDigimon().modeChange();
        this._currentMenu = Enum.Menu.None;
    }

    public void onPrize() {
        this._currentMenu = Enum.Menu.TrophyPrizeBits;
    }

    public void onBattleLevel() {
        this._currentMenu = Enum.Menu.Data_BattleLevels;
    }

    public void onCalories() {
        this._currentMenu = Enum.Menu.Food_Calories;
    }

    public void onDigimonCalories() {
        this._currentMenu = Enum.Menu.Data_Calories;
    }

    public void onNutrition() {
        switch (this._currentMenu) {
            case Data_Hunger: {
                this._currentMenu = Enum.Menu.Data_Nutrition;
                break;
            }
            case Buy_Food: {
                this._currentMenu = Enum.Menu.Buy_Nutrition;
                break;
            }
            case Use_Food: {
                this._currentMenu = Enum.Menu.Use_Nutrition;
                break;
            }
            case Use_Med_Food: {
                this._currentMenu = Enum.Menu.Med_Nutrition;
                break;
            }
            case Sell_Food: {
                this._currentMenu = Enum.Menu.Sell_Nutrition;
            }
        }
    }

    public void onCardOption() {
        switch (this._currentMenu) {
            case Battle_Validation: {
                this._currentMenu = Enum.Menu.Card_Options;
                break;
            }
            case DNA_Validation: {
                this._currentMenu = Enum.Menu.DNA_Inventory;
                break;
            }
            case EvolutionMenu: {
                this._view.setConsumablePage(false, false, 0, Item.class);
                this._currentMenu = Enum.Menu.EvolutionInventory;
            }
        }
    }

    public void onCardShop() {
        this._currentMenu = Enum.Menu.Card_Shop;
    }

    public void onTourneyOption() {
        switch (this._currentMenu) {
            case Food_Buy_Sell_Validation: {
                this._view.setConsumablePage(true, false, 0, FoodType.class);
                this._model.getDigimon().restockFoodShop();
                this._currentMenu = Enum.Menu.Food_Shop;
                break;
            }
            case Item_Buy_Sell_Validation: {
                this._view.setConsumablePage(true, false, 0, Item.class);
                this._model.getDigimon().restockItemShop();
                this._currentMenu = Enum.Menu.Item_Shop;
                break;
            }
            default: {
                this._currentMenu = Enum.Menu.Tourney_Options;
            }
        }
    }

    public void onTourneyRecords() {
        this._currentMenu = Enum.Menu.Season_Records;
    }

    public void onSeason() {
        this._currentMenu = this._currentMenu == Enum.Menu.Data_Temp ? Enum.Menu.None : Enum.Menu.Data_Temp;
    }

    public void onSeasonRecords(Enum.Season s) {
        switch (s) {
            case Spring: {
                this._currentMenu = Enum.Menu.Spring_Records;
                break;
            }
            case Summer: {
                this._currentMenu = Enum.Menu.Summer_Records;
                break;
            }
            case Fall: {
                this._currentMenu = Enum.Menu.Fall_Records;
                break;
            }
            case Winter: {
                this._currentMenu = Enum.Menu.Winter_Records;
            }
        }
    }

    public void onPrelimDetails() {
        Tournament tournament = this._model.getDigimon().getTournament();
        Trophy t = tournament.getCurrentTrophy();
        tournament.setCurrentTrophy(tournament.getTrophy(t.getPrelim()));
        if (this._currentMenu == Enum.Menu.Tourney_Registration) {
            this._currentMenu = Enum.Menu.Registration_Prelim_Details;
        } else if (this._currentMenu == Enum.Menu.TrophyDetails) {
            this._currentMenu = Enum.Menu.Records_Prelim_Details;
        } else if (this._currentMenu == Enum.Menu.Records_Prelim_Details || this._currentMenu == Enum.Menu.Registration_Prelim_Details) {
            this._view.drawTrophyPrelimDetails();
        }
    }

    public void onTrophyDetails(Trophy trophy) {
        if (trophy != null) {
            switch (this._currentMenu) {
                case Tourney_Enter: {
                    this._model.getDigimon().getTournament().setCurrentTrophy(trophy);
                    this._currentMenu = Enum.Menu.Tourney_Registration;
                    break;
                }
                default: {
                    this._model.getDigimon().getTournament().setCurrentTrophy(trophy);
                    this._currentMenu = Enum.Menu.TrophyDetails;
                }
            }
        }
    }

    public void onTourneyEnter() {
        this._currentMenu = Enum.Menu.Tourney_Enter;
    }

    public Trophy checkTrophy(int spriteNum, int spriteSet) {
        Trophy trophy = null;
        switch (this._currentMenu) {
            case Spring_Records: {
                trophy = this._model.getDigimon().getTournament().getTrophy(spriteNum, spriteSet, Enum.Season.Spring);
                break;
            }
            case Summer_Records: {
                trophy = this._model.getDigimon().getTournament().getTrophy(spriteNum, spriteSet, Enum.Season.Summer);
                break;
            }
            case Winter_Records: {
                trophy = this._model.getDigimon().getTournament().getTrophy(spriteNum, spriteSet, Enum.Season.Winter);
                break;
            }
            case Fall_Records: {
                trophy = this._model.getDigimon().getTournament().getTrophy(spriteNum, spriteSet, Enum.Season.Fall);
                break;
            }
            default: {
                trophy = this._model.getDigimon().getTournament().getTrophy(spriteNum, spriteSet, this._model.getDigimon().getSeason());
            }
        }
        return trophy;
    }

    public void onStartBattleFinish() {
        if (!this._model.getDigimon().getIsFree()) {
            this._currentMenu = Enum.Menu.Attack_Validation;
        } else {
            this.chooseAttack(Enum.Attribute.None, true, false);
        }
    }

    private void chooseAttack(Enum.Attribute att, boolean free, boolean skip) {
        if (!this._battle.chooseAttack(att, free, skip)) {
            this.refusedAttackFeedback();
        }
        if (this._battle.getBattleType() == Battle.BattleType.PvP) {
            this.onTurnWait(this._battle.getAttackType().ordinal());
        } else {
            this.onFight();
        }
    }

    public void onAttack() {
        this._currentMenu = Enum.Menu.AttackType_Validation;
    }

    public void onVaccineAttack() {
        this.chooseAttack(Enum.Attribute.Vaccine, false, false);
    }

    public void onDataAttack() {
        this.chooseAttack(Enum.Attribute.Data, false, false);
    }

    public void onVirusAttack() {
        this.chooseAttack(Enum.Attribute.Virus, false, false);
    }

    private void refusedAttackFeedback() {
        this._view.setMessage("Your Digimon ignored your order");
    }

    public void onTurnWait(final int playerAttack) {
        this._turnWait = true;
        this._view.endAnim();
        this._model.getDigimon().setCurrentState(Enum.State.WaitingTurn);
        this._currentMenu = Enum.Menu.None;
        Thread thread = new Thread(new Runnable(){
            final /* synthetic */ ClockTic this$0;
            {
                this.this$0 = this$0;
            }

            @Override
            public void run() {
                while (this.this$0._turnWait) {
                    Enum.Attribute att;
                    if (this.this$0._hostBattle != null && ((ClockTic)this.this$0)._hostBattle._output != null) {
                        att = this.this$0._hostBattle.waitTurn(playerAttack);
                        this.this$0._battle.setOppAttack(att);
                        this.this$0._turnWait = att == Enum.Attribute.NA;
                        try {
                            this.this$0._battle.checkFirst(false);
                            ((ClockTic)this.this$0)._hostBattle._output.writeBoolean(this.this$0._battle.getPlayerFirst());
                        }
                        catch (Exception e) {
                            e.printStackTrace();
                            this.this$0.onError(true);
                        }
                        continue;
                    }
                    if (this.this$0._connectBattle == null || ((ClockTic)this.this$0)._connectBattle._input == null) continue;
                    att = this.this$0._connectBattle.waitTurn(playerAttack);
                    this.this$0._battle.setOppAttack(att);
                    this.this$0._turnWait = att == Enum.Attribute.NA;
                    try {
                        this.this$0._battle.setPlayerFirst(!((ClockTic)this.this$0)._connectBattle._input.readBoolean());
                    }
                    catch (Exception e) {
                        e.printStackTrace();
                        this.this$0.onError(true);
                    }
                }
                if (this.this$0._battle.getInProgress()) {
                    this.this$0.onFight();
                }
            }
        });
        thread.start();
    }

    public void onFight() {
        this._view.endAnim();
        this._battle.attack();
        this._battle.processState();
        this._currentMenu = Enum.Menu.None;
    }

    public void onRoundEnd() {
        this._battle.resetTurn();
        this._model.getDigimon().checkSurrender(this._battle);
        switch (this._model.getDigimon().getSurrender()) {
            case 0: {
                if (!this._model.getDigimon().getIsFree()) {
                    this._currentMenu = Enum.Menu.Attack_Validation;
                    break;
                }
                this.chooseAttack(Enum.Attribute.None, true, false);
                break;
            }
            case 2: {
                this._view.setMessage("Your Digimon wants to give up");
                this._currentMenu = Enum.Menu.Surrender_Validation;
                break;
            }
            default: {
                this._currentMenu = Enum.Menu.Surrender_Validation;
                this.onYes();
                this._view.setMessage("Your Digimon ran from battle");
                this._model.getDigimon().setScold(true);
            }
        }
    }

    public void verifyBackNoAnim() {
        PhysicalState digimon = this._model.getDigimon();
        if (!this.verifyBackground(digimon.getWorld().getCurrentZone(), digimon)) {
            this._view.getBackgroundAnim().checkBackNoAnim(digimon, this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
        }
    }

    public boolean onBattleEnd() {
        boolean won = false;
        PhysicalState digimon = this._model.getDigimon();
        WorldMap world = digimon.getWorld();
        if (this._battle != null) {
            Enemy e = this._battle.getEnemy();
            Battle.BattleType bt = this._battle.getBattleType();
            won = this._battle.battleEnd();
            if (bt == Battle.BattleType.PvE_Wild) {
                if (!won) {
                    world.setAdventureLife(world.getAdventureLife() - 1);
                    if (world.getAdventureLife() > 0) {
                        world.lossPenalty(e.getPenalty());
                        this.verifyBackNoAnim();
                    }
                } else if (won && !e.getIsRandom()) {
                    e.startCooldown();
                    if (e.getIsZoneBoss()) {
                        world.setAdventureLife(Config._maxAdventureLife);
                    }
                    world.incSteps(world.getCurrentZone());
                }
                if (won || world.getAdventureLife() > 0) {
                    // empty if block
                }
                if (this._battle.getBitsWon() > 0) {
                    this._numHits = this._battle.getBitsWon();
                }
                if (this._battle.getItem() != null) {
                    digimon.setUnlockConsumable(this._battle.getItem().getConsumableID());
                }
            } else if (bt == Battle.BattleType.PvP) {
                this.endConnection();
            }
            if (this._battle.getBattleRecord() != null) {
                this._battle.addToBattleRecord(this.getBattleRecordEnd(won));
                this.recordBattle(this._battle.getBattleRecord());
                this._battle.getBattleRecord().clear();
            }
            this.resetBattle();
        }
        return won;
    }

    private void resetBattle() {
        this._previousEnemy = this._battle.getEnemy().getIndex();
        this._battle = null;
    }

    private void checkBattleRecordFile(String filename, File log) {
        if (!log.exists() || log.exists() && log.length() >= 1000000L) {
            if (log.exists()) {
                log.delete();
            }
            try {
                FileWriter newFile = new FileWriter(filename);
                newFile.close();
            }
            catch (IOException ex) {
                Logger.getLogger(CrashEntry.class.getName()).log(Level.SEVERE, null, ex);
            }
        }
    }

    private String[] getBattleInfo(PhysicalState digimon) {
        if (this._battle != null) {
            Enemy e = this._battle.getEnemy();
            String player = digimon.getName() + " (P): HP - " + this._battle.getFullHealth() + " | Vaccine - " + this._battle.getRed() + " | Data - " + this._battle.getGreen() + " | Virus - " + this._battle.getYellow();
            String opponent = (this._battle.getEnemy().getIndex() >= 0 ? digimon.getEvolution().getDigimon(e.getIndex()).getName() : "Punching Bag") + " (O): HP - " + e.getEnemyHealth() + " | Vaccine - " + e.getOppRed() + " | Data - " + e.getOppGreen() + " | Virus - " + e.getOppYellow();
            return new String[]{player, opponent, "", "*************", ""};
        }
        return new String[]{"null", "null", "", "*************", ""};
    }

    private String[] getMultiInfo(PhysicalState digimon) {
        String[] record = new String[14];
        String checksum = "";
        boolean gameMod = false;
        int diff = -1;
        if (this._hostBattle != null) {
            record[0] = "Host";
            record[1] = "";
            record[2] = "Player IP: " + this._hostBattle.getClientSocket().getLocalAddress().getHostAddress();
            record[3] = "";
            record[4] = "Opponent IP: " + this._hostBattle.getClientSocket().getInetAddress().getHostAddress();
            checksum = this._hostBattle.getOppChecksum();
            gameMod = this._hostBattle.getOppGameMod();
            diff = this._hostBattle.getOppDiff();
        } else if (this._connectBattle != null) {
            record[0] = "Connecting";
            record[1] = "";
            record[2] = "Player IP: " + this._connectBattle.getClientSocket().getLocalAddress();
            record[3] = "";
            record[4] = "Opponent IP: " + this._connectBattle.getSocketAddress().getHostName();
            checksum = this._connectBattle.getOppChecksum();
            gameMod = this._connectBattle.getOppGameMod();
            diff = this._connectBattle.getOppDiff();
        }
        record[5] = "";
        record[6] = "Player's Checksum: " + digimon.getChecksum();
        record[7] = "The player's game has " + (digimon.getGameModified() ? "been" : "not been") + " modified since this save file was created";
        record[8] = "The player is using the " + (digimon.getDifficultySetting() == 0 ? "Hard" : (digimon.getDifficultySetting() == 2 ? "Hardcore" : "Classic")) + " difficulty setting";
        record[9] = "";
        record[10] = "Opponent's Checksum: " + checksum;
        record[11] = "The opponent's game has " + (gameMod ? "been" : "not been") + " modified since this save file was created";
        record[12] = "The opponent is using the " + (diff == 0 ? "Hard" : (diff == 2 ? "Hardcore" : "Classic")) + " difficulty setting";
        record[13] = "";
        if (this._battle != null) {
            this._battle.setOppDifficulty(diff);
        }
        return record;
    }

    private void recordBattle(ArrayList<String> record) {
        String filename = "files/battleRecord.txt";
        File log = new File(filename);
        this.checkBattleRecordFile(filename, log);
        if (log.exists()) {
            Calendar cal = Calendar.getInstance();
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy_MM_dd HH:mm:ss");
            String entry = sdf.format(cal.getTime());
            try (BufferedWriter save = new BufferedWriter(new FileWriter(filename, true));){
                save.newLine();
                save.write(entry);
                save.newLine();
                for (String s : record) {
                    save.write(s);
                    save.newLine();
                }
            }
            catch (IOException exc) {
                exc.printStackTrace();
            }
        }
    }

    private String[] getBattleRecordEnd(boolean isWon) {
        return new String[]{"Player " + (isWon ? "Won" : "Lost"), "------------------------------------------------------"};
    }

    private void recordBattle(String s) {
        String filename = "files/battleRecord.txt";
        File log = new File(filename);
        this.checkBattleRecordFile(filename, log);
        if (log.exists()) {
            try (BufferedWriter save = new BufferedWriter(new FileWriter(filename, true));){
                save.newLine();
                save.write(s);
                save.newLine();
                save.write("------------------------------------------------------");
            }
            catch (IOException exc) {
                exc.printStackTrace();
            }
        }
    }

    private void endConnection() {
        try {
            if (this._hostBattle != null) {
                this._hostBattle.dispose();
                this._hostBattle = null;
            } else if (this._connectBattle != null) {
                this._connectBattle.dispose();
                this._connectBattle = null;
            } else if (this._hostJogress != null) {
                this._hostJogress.dispose();
                this._hostJogress = null;
            } else if (this._connectJogress != null) {
                this._connectJogress.dispose();
                this._connectJogress = null;
            }
            this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
    }

    public void onSurrender() {
        if (this._currentMenu == Enum.Menu.Attack_Validation) {
            PhysicalState digimon = this._model.getDigimon();
            digimon.checkRefused(null, null, true, 0.0);
            if (!digimon.getRefused() || digimon.getSurrender() == 2) {
                this._currentMenu = Enum.Menu.Surrender_Validation;
            } else {
                this._sounds.playSound(SoundConfig._refuseSurrender);
                this._view.setMessage("Your Digimon doesn't want to give up");
                this._model.getDigimon().setScold(true);
                this.chooseAttack(Enum.Attribute.None, true, false);
            }
            digimon.setRefused(false);
        }
    }

    public void onDie(boolean dead) {
        PhysicalState digimon = this._model.getDigimon();
        if (dead) {
            digimon.setAlive(false);
            if (digimon.getBonus() > 0) {
                digimon.setCurrentState(Enum.State.UnlockInheritance);
            }
            this.leaveTourney(digimon);
        } else {
            digimon.saveFromDeath();
        }
        digimon.autoSave();
        this._numHits = 0;
        this._currentMenu = Enum.Menu.None;
    }

    public void leaveTourney(PhysicalState digimon) {
        if (digimon.getTournament().getActive()) {
            this.setupTourneyBattle(digimon);
            this._view.setSpriteCharDefault();
            this._battle.surrender();
            digimon.getTournament().getChecked().add(digimon.getTournament().getCurrentEnemy());
            digimon.getTournament().setIsWon(0);
            digimon.setCurrentState(Enum.State.NPC_Fight);
            this.resetBattle();
            this._currentMenu = Enum.Menu.None;
        }
    }

    private void surrenderEffect(PhysicalState digimon) {
        Battle.BattleType type = this._battle.getBattleType();
        if (digimon.getSurrender() == 2 || digimon.getSurrender() == 1) {
            digimon.setMood(digimon.getMood() + Config._surrenderEffectMoodInc);
            if (digimon.getSurrender() == 1 && digimon.getDisposition() < 0 && this._battle.getHealth() >= this._battle.getEnemyHealth()) {
                digimon.setMood(digimon.getMood() - Config._surrenderEffectLowDispositionMoodDec);
            }
            if (this._battle.getHealth() >= this._battle.getEnemyHealth()) {
                digimon.setObedience(digimon.getObedience() - (digimon.getSurrender() == 2 ? Config._surrenderEffectRequestObedienceDec : Config._surrenderEffectObedienceDec));
            }
            if (digimon.getSurrender() == 2 && this._battle.getHealth() < this._battle.getEnemyHealth()) {
                digimon.setObedience(Config._surrenderEffectRequestLowHealthObedienceInc);
            }
        }
        this.recordBattle(this._battle.getBattleRecord());
        this._battle.getBattleRecord().clear();
        this._battle.surrender();
        this._view.endAnim();
        this._currentMenu = Enum.Menu.None;
        this.resetBattle();
        if (type != Battle.BattleType.PvE_Wild) {
            if (digimon.getDisposition() == -1) {
                digimon.setCurrentState(Enum.State.Jeering);
            } else {
                digimon.setCurrentState(Enum.State.Sad_Jeering);
            }
        } else {
            this.verifyBackground(digimon.getWorld().getCurrentZone(), digimon);
            digimon.setCurrentState(Enum.State.Retreating);
        }
    }

    public boolean onYes() {
        boolean success = true;
        PhysicalState digimon = this._model.getDigimon();
        block2 : switch (this._currentMenu) {
            case SaveExit_Validation: {
                this._model.getDigimon().save(true);
                break;
            }
            case DigiMemory_Validation: {
                digimon.setNewDigimemory();
                this._currentMenu = Enum.Menu.None;
                break;
            }
            case Clock_Validation: {
                if ((Config._clockCanChangeDuringCountdown || this._model.getTime().getTimeChanged() <= 0) && this._model.getTime().timeChanged()) {
                    this._model.getTime().checkCheating(this._model.getDigimon());
                    this._model.getTime().setRawSeconds((byte)0);
                    this._model.getTime().setNanoRemainder(0L, this.isPlaying(), this._model.getDigimon());
                    this._currentMenu = Enum.Menu.None;
                    this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
                    break;
                }
                success = false;
                break;
            }
            case Investigate_Validation: {
                this._view.setFrame(0);
                Zone z = digimon.getWorld().getCurrentZone();
                int[] c = z.checkItem();
                if (c != null) {
                    digimon.setGift(c);
                    digimon.setCurrentState(Enum.State.Discovering);
                } else {
                    digimon.setCurrentState(Enum.State.DiscoverEnemy);
                }
                this._currentMenu = Enum.Menu.None;
                break;
            }
            case Tourney_Validation: {
                if (digimon.canBattle(true)) {
                    Tournament t = this._model.getDigimon().getTournament();
                    digimon.getWorld().setTravelSpeed((byte)0);
                    t.setActive(true);
                    this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
                    this._view.setFrame(0);
                    this._view.setCurrentAnim(null);
                    digimon.setCurrentState(Enum.State.Tourney_Start);
                    this._currentMenu = Enum.Menu.None;
                    break;
                }
                this._currentMenu = Enum.Menu.None;
                break;
            }
            case Tourney_Surrender: {
                this._view.endAnim();
                this.onTourneyBattle();
                this._view.setSpriteCharDefault();
                this.surrenderEffect(digimon);
                digimon.getTournament().getChecked().add(digimon.getTournament().getCurrentEnemy());
                digimon.getTournament().setIsWon(0);
                digimon.setCurrentState(Enum.State.NPC_Fight);
                break;
            }
            case Battle_Style: {
                digimon.setIsFree(!digimon.getIsFree());
                this._view.drawBattleStyleMenu();
                break;
            }
            case Surrender_Validation: {
                this._view.setSpriteCharDefault();
                if (this._battle == null) break;
                switch (this._battle.getBattleType()) {
                    case PvE_Wild: {
                        boolean surrendered = digimon.canEscape(this._battle.getEnemy());
                        if (surrendered) {
                            digimon.getWorld().lossPenalty(this._battle.getEnemy().getPenalty());
                            this.surrenderEffect(digimon);
                            break block2;
                        }
                        this._view.setMessage("Your Digimon tried to escape but failed");
                        this.chooseAttack(Enum.Attribute.None, true, true);
                        break block2;
                    }
                    case PvE_Tourney: {
                        digimon.getTournament().getChecked().add(digimon.getTournament().getCurrentEnemy());
                        digimon.getTournament().setIsWon(0);
                        digimon.setCurrentState(Enum.State.NPC_Fight);
                        this.surrenderEffect(digimon);
                        break block2;
                    }
                    case PvP: {
                        if (this._hostBattle != null) {
                            try {
                                this._hostBattle._output.writeBoolean(true);
                            }
                            catch (Exception e) {
                                CrashEntry.generateEntry(e);
                                e.printStackTrace();
                            }
                        } else if (this._connectBattle != null) {
                            try {
                                this._connectBattle._output.writeBoolean(true);
                            }
                            catch (Exception e) {
                                CrashEntry.generateEntry(e);
                                e.printStackTrace();
                            }
                        }
                        this._battle.getBattleRecord().add("Surrendered");
                        this._battle.getBattleRecord().add("------------------------------------------------------");
                        this.endConnection();
                        this.surrenderEffect(digimon);
                        this._view.resetScreen();
                        this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
                        break block2;
                    }
                }
                this.surrenderEffect(digimon);
                break;
            }
            case Restart: {
                this._currentMenu = Enum.Menu.Choose_Egg;
                break;
            }
            case Zone_Validation: 
            case Zone_Validation_Ticket: {
                Item zoneTicket = this._view.getItemType();
                if (zoneTicket == null || zoneTicket.getAnim() != Enum.State.PhoenixTransport) {
                    for (Item i : digimon.getItems()) {
                        if (i.getAnim() != Enum.State.PhoenixTransport) continue;
                        zoneTicket = i;
                        this._view.setItemType(i);
                        break;
                    }
                }
                if (zoneTicket != null && zoneTicket.getAnim() == Enum.State.PhoenixTransport && zoneTicket.getCurrentUses() > 0) {
                    digimon.setBattleImmunity(true);
                    Item item = this._view.getItemType();
                    if (item == null) {
                        item = zoneTicket;
                    }
                    digimon.useItem(item);
                    this._currentMenu = Enum.Menu.None;
                    break;
                }
                success = false;
                break;
            }
            case Map_Validation: 
            case Map_Validation_Ticket: {
                Item ticket = this._view.getItemType();
                if (ticket == null || ticket.getAnim() != Enum.State.WhaTransport) {
                    for (Item i : digimon.getItems()) {
                        if (i.getAnim() != Enum.State.WhaTransport) continue;
                        ticket = i;
                        this._view.setItemType(i);
                        break;
                    }
                }
                if (ticket != null && ticket.getAnim() == Enum.State.WhaTransport && ticket.getCurrentUses() > 0) {
                    if (this._currentMenu == Enum.Menu.Map_Validation) {
                        this._view.setConsumablePage(this._view.getConsumablePage() - 1);
                    }
                    digimon.setBattleImmunity(true);
                    Item item = this._view.getItemType();
                    if (item == null) {
                        item = ticket;
                    }
                    digimon.useItem(item);
                    this._currentMenu = Enum.Menu.None;
                    break;
                }
                success = false;
            }
        }
        return success;
    }

    public void onNo() {
        switch (this._currentMenu) {
            case SaveExit_Validation: {
                this._currentMenu = Enum.Menu.Save_Validation;
                break;
            }
            case DigiMemory_Validation: {
                this._currentMenu = Enum.Menu.None;
                break;
            }
            case Clock_Validation: {
                this._model.getTime().resetTime();
                this._currentMenu = Enum.Menu.None;
                break;
            }
            case Investigate_Validation: {
                this._currentMenu = Enum.Menu.None;
                break;
            }
            case Tourney_Validation: {
                this._currentMenu = Enum.Menu.Tourney_Registration;
                break;
            }
            case Tourney_Surrender: {
                this._currentMenu = Enum.Menu.Roster;
                break;
            }
            case Surrender_Validation: {
                PhysicalState digimon = this._model.getDigimon();
                if (digimon.getSurrender() == 2) {
                    digimon.setMood(digimon.getMood() - Config._surrenderRejectMoodDec);
                    digimon.setObedience(digimon.getObedience() + Config._surrenderRejectObedienceInc);
                }
                if (!digimon.getIsFree()) {
                    this._currentMenu = Enum.Menu.Attack_Validation;
                    break;
                }
                this.chooseAttack(Enum.Attribute.None, true, false);
                break;
            }
            case Restart: {
                this._currentMenu = Enum.Menu.PraiseScold_Validation;
                break;
            }
            case Zone_Validation: {
                this._currentMenu = Enum.Menu.MapZoneSelect;
                break;
            }
            case Zone_Validation_Ticket: {
                this._currentMenu = Enum.Menu.ChooseZone;
                break;
            }
            case Map_Validation: {
                this._currentMenu = Enum.Menu.WorldMapSelect;
                break;
            }
            case Map_Validation_Ticket: {
                this._currentMenu = Enum.Menu.WorldMapSelect_Ticket;
            }
        }
    }

    public void onChooseEgg() {
        switch (this._currentMenu) {
            case Choose_Egg: {
                this._currentMenu = Enum.Menu.None;
                this._view.endAnim();
                this._model.getDigimon().setDigimon(this._model.getDigimon().getEvolution().getRestartDigimon().get(this._view.getConsumablePage()), true);
                this._view.changeSprite();
            }
        }
    }

    public void onCards() {
    }

    public void onHPTrainingAttribute(Enum.Attribute a) {
        ++this._trainingRound;
        this._barSize = a.ordinal();
        this._view.endAnim();
        if (Enum.Attribute.values()[this._numHits] == a) {
            this._model.getDigimon().setPriorityState(Enum.State.HP_Training_AttackSuccess);
            ++this._trainingRoundsWon;
        } else {
            this._model.getDigimon().setPriorityState(Enum.State.HP_Training_AttackFail);
        }
        this._view.disposeMusic();
    }

    public boolean onPreTrain(Enum.Attribute attribute) {
        boolean canTrain = false;
        this._view.endAnim();
        if (this._model.getDigimon().canExercise(attribute)) {
            this.slowClock();
            this._currentMenu = Enum.Menu.None;
            canTrain = true;
            this._shieldActiveTop = true;
            this._numHits = 0;
            this._barSize = 0;
            this._trainingRound = 0;
            this._trainingRoundsWon = 0;
        } else {
            this._currentMenu = Enum.Menu.None;
        }
        return canTrain;
    }

    public void onShield() {
        this._shieldActiveTop = !this._shieldActiveTop;
    }

    public void onHit(Enum.State s) {
        switch (s) {
            case Virus_Training: {
                this._view.endAnim();
                this.onPreFinish(Enum.Attribute.Virus);
                break;
            }
            case Vaccine_Training: 
            case DNA_Generate: {
                ++this._numHits;
            }
        }
    }

    public void onPreFinish(Enum.Attribute attribute) {
        try {
            this._keyboard.clearInteractiveButtons();
        }
        catch (ArrayIndexOutOfBoundsException arrayIndexOutOfBoundsException) {
            // empty catch block
        }
        this._view.setSuccess(this.checkSuccess(attribute));
        this._model.getDigimon().setCurrentState(Enum.State.Attacking);
    }

    public void onAttackEnd() {
        this._model.getDigimon().setCurrentState(Enum.State.Attack_Contact);
    }

    public void onHitEnd() {
        this._model.getDigimon().setCurrentState(Enum.State.Attack_Aftermath);
    }

    public boolean checkSuccess(Enum.Attribute attribute) {
        boolean success = false;
        boolean isUp = this._view.getUp();
        switch (attribute) {
            case None: {
                success = this._trainingRoundsWon >= Config._hpTrainingRoundsWon;
                break;
            }
            case Vaccine: {
                int rank = this._model.getDigimon().getVaccinePower() / Config._attributeTrainDifficultyChange;
                byte hits = 0;
                switch (rank) {
                    case 0: {
                        hits = Config._vaccineGameHitsMinEasy;
                        break;
                    }
                    case 1: {
                        hits = Config._vaccineGameHitMin;
                        break;
                    }
                    default: {
                        hits = Config._vaccineGameHitsMinHard;
                    }
                }
                if (this._numHits < hits) break;
                success = true;
                break;
            }
            case Data: {
                if ((!this._shieldActiveTop || !isUp) && (this._shieldActiveTop || isUp)) break;
                success = true;
                break;
            }
            case Virus: {
                if (this._barSize < Config._virusGameBarMin) break;
                success = true;
            }
        }
        return success;
    }

    public void onExerciseFinish(Enum.Attribute attribute) {
        PhysicalState digimon = this._model.getDigimon();
        boolean complied = digimon.checkCompliant();
        digimon.exercise(attribute, complied);
        digimon.incAttRank(attribute);
        if (this._view.getSuccess()) {
            if (complied) {
                digimon.changeTrainingRank(attribute, Config._rankChangeTrainForced);
            }
            digimon.setPraise(true);
            switch (attribute) {
                case Vaccine: {
                    digimon.setVaccinePower(this._model.getDigimon().getVaccinePower() + 1);
                    break;
                }
                case Virus: {
                    digimon.setVirusPower(this._model.getDigimon().getVirusPower() + 1);
                    break;
                }
                case Data: {
                    digimon.setDataPower(this._model.getDigimon().getDataPower() + 1);
                    break;
                }
                case None: {
                    digimon.checkAndIncPerfectWins(Config._practiceAlwaysIncPerfectWins);
                }
            }
        } else {
            digimon.changeTrainingRank(attribute, Config._rankChangeTrainFail + (complied ? Config._rankChangeTrainForced : (byte)0));
            digimon.setMood(digimon.getMood() - Config._exerciseFailMoodDec);
            digimon.setObedience(digimon.getObedience() - Config._exerciseFailObedienceDec);
            digimon.setCurrentState(Enum.State.Jeering);
        }
        digimon.autoSave();
    }

    public void onDataFavorites() {
        this._currentMenu = Enum.Menu.Data_Dislikes;
    }

    public void onEvolButton() {
        this._currentMenu = Enum.Menu.EvolutionTree;
        this.initEvolutionTree();
    }

    private void initEvolutionTree() {
        if (this._tree == null) {
            this._tree = new EvolutionTree(this._model.getDigimon(), this, (byte)this._model.getSettings().getGameScale(), this._model.getSettings().isSound(), this._view.getModFolder(), this._view.getResourcesFolder(), this._keyboard, this._sounds, this._view.getFoodLabel(), this._view.getItemLabel(), this._model.getDigimon().getHabitats());
            this.setWindowLoc();
            this._view.setVisible(false);
        } else {
            this._tree.setVisible(true);
        }
    }

    private void setWindowLoc() {
        try {
            this._windowLocX = this._view.getLocationOnScreen().x;
            this._windowLocY = this._view.getLocationOnScreen().y;
        }
        catch (IllegalComponentStateException e) {
            e.printStackTrace();
        }
    }

    public void onMapButton() {
        this._currentMenu = Enum.Menu.MapZoneSelect;
    }

    public void onMapChange() {
        if (this._model.getDigimon().getIsHome()) {
            this._currentMenu = Enum.Menu.None;
            if (this._model.getDigimon().canTeleport()) {
                this._model.getDigimon().setCurrentState(Enum.State.Teleport_Leave);
            }
        } else {
            this._view.setConsumablePage(0);
            this._currentMenu = Enum.Menu.WorldMapSelect;
        }
    }

    public void onZone(boolean isCurrent) {
        switch (this._currentMenu) {
            case MapZoneSelect: {
                if (isCurrent) {
                    this._currentMenu = Enum.Menu.ZoneDetail;
                    break;
                }
                this._currentMenu = Enum.Menu.Zone_Validation;
                break;
            }
            case ChooseZone: {
                if (isCurrent) break;
                this._currentMenu = Enum.Menu.Zone_Validation_Ticket;
            }
        }
    }

    public void onMapSelect() {
        switch (this._currentMenu) {
            case WorldMapSelect: {
                if (this._view.getConsumablePage() == 0) {
                    this._currentMenu = Enum.Menu.None;
                    if (!this._model.getDigimon().canTeleport()) break;
                    this._model.getDigimon().setCurrentState(Enum.State.Teleport_Leave);
                    break;
                }
                this._currentMenu = Enum.Menu.Map_Validation;
                break;
            }
            case WorldMapSelect_Ticket: {
                this._currentMenu = Enum.Menu.Map_Validation_Ticket;
            }
        }
    }

    public void onClockButton() {
        if (!this._model.getDigimon().isPaused()) {
            this._currentMenu = Enum.Menu.Set_Clock;
            this._model.getTime().setMinuteBeforeChange(this._model.getTime().getTotalMinutesOfDay());
        } else {
            this.onPause();
        }
    }

    public void requestViewFocus() {
        this._view.requestFocus();
    }

    public void onTourneyAlarm(int id) {
        if (id == this._model.getDigimon().getTourneyAlarm()) {
            this._model.getDigimon().setTourneyAlarm(-1);
        } else {
            this._model.getDigimon().setTourneyAlarm(id);
        }
    }

    public void onAutoCareValidation() {
        this._currentMenu = Enum.Menu.Set_AutoCare;
    }

    public void onAlarmSwitch() {
        if (this._model.getTime().getAlarmMinutes() >= 0) {
            this._model.getTime().setAlarmMinutes(-1);
        } else {
            String[] time = this._view.getTimeFromPanel().split(":");
            this._model.getTime().setAlarmMinutes(this._model.getTime().getTotalMinutesOfDay(Integer.parseInt(time[0]), Integer.parseInt(time[1])));
        }
    }

    public boolean onPause() {
        if ((this._currentMenu == Enum.Menu.None || this._currentMenu == Enum.Menu.Set_Clock) && this._model.getDigimon().getAlive()) {
            if (this._model.getDigimon().isPaused()) {
                this._view.endAnim();
                this._view.setCurrentAnim(Enum.State.Unpausing);
                this._model.getDigimon().setCurrentState(Enum.State.Unpausing);
            } else {
                this._currentMenu = Enum.Menu.None;
                this._model.getDigimon().setCurrentState(Enum.State.Pausing);
            }
            return true;
        }
        return false;
    }

    public void onPauseFinished() {
        this._model.getDigimon().setPaused(true);
    }

    public void onUnpauseFinished() {
        this._model.getDigimon().setPaused(false);
    }

    public void onSettingsButton() {
        this._currentMenu = Enum.Menu.Settings;
    }

    public void onScale(byte newScale) {
        this._newScale = newScale;
    }

    public Shell getCurrentShell() {
        if (this._model.getSettings().getShell() < this._shells.size()) {
            return this._shells.get(this._model.getSettings().getShell());
        }
        return this._shells.get(0);
    }

    public void setShell(int shell) {
        this._model.getSettings().setShell(shell);
    }

    public void onSound() {
        this._model.getSettings().setSound(!this._model.getSettings().isSound());
    }

    public void onFocusCall() {
        this._model.getSettings().setFocus(!this._model.getSettings().isFocus());
    }

    public void onOnTop() {
        this._model.getSettings().setOnTop(!this._model.getSettings().isOnTop());
        this._view.setAlwaysOnTop(this._model.getSettings().isOnTop());
    }

    public void onSaveButton() {
        this._currentMenu = Enum.Menu.Save_Validation;
    }

    public void onSave() {
        this._model.getDigimon().save(false);
        this._view.setMessage("&nbsp; &nbsp;&nbsp;&nbsp;Game<br>&nbsp; &nbsp;&nbsp;&nbsp;Saved");
        this._currentMenu = Enum.Menu.None;
    }

    public void onQuit() {
        if (Config._validateSaveExit) {
            this._currentMenu = Enum.Menu.SaveExit_Validation;
        } else {
            this._model.getDigimon().save(true);
        }
    }

    public void onHabitat() {
        switch (this._currentMenu) {
            case Shop_Validation: {
                this._currentMenu = Enum.Menu.Habitat_Shop;
                break;
            }
            case Inventory_Validation: {
                this._currentMenu = Enum.Menu.Habitat_Inventory;
            }
        }
    }

    public void onItem() {
        switch (this._currentMenu) {
            case Shop_Validation: {
                PhysicalState digimon = this._model.getDigimon();
                if (digimon.getCanSell(false)) {
                    this._currentMenu = Enum.Menu.Item_Buy_Sell_Validation;
                    break;
                }
                this._currentMenu = Enum.Menu.Item_Shop;
                break;
            }
            case Inventory_Validation: {
                this._view.setConsumablePage(false, false, 0, Item.class);
                this._currentMenu = Enum.Menu.Item_Inventory;
            }
        }
    }

    public void onHealthBar() {
        this._currentMenu = Enum.Menu.Data_HealthTrack;
    }

    public void onBack() {
        PhysicalState digimon = this._model.getDigimon();
        switch (this._currentMenu) {
            case Data_Calories: 
            case Food_Calories: {
                this._currentMenu = this._menuHistory[1];
                break;
            }
            case Data_Likes: 
            case Data_Dislikes: 
            case Data_SpeciesLikes: 
            case Data_SpeciesDislikes: 
            case Data_Intolerant: {
                this._currentMenu = Enum.Menu.Data_Person;
                break;
            }
            case Data_Person_Detail: {
                this._currentMenu = this._menuHistory[1];
                break;
            }
            case Choose_Egg: {
                this._currentMenu = Enum.Menu.PraiseScold_Validation;
                break;
            }
            case ChooseZone: {
                this._currentMenu = Enum.Menu.Use_Item;
                break;
            }
            case Data_BattleLevels: {
                this._currentMenu = Enum.Menu.Data_Battles;
                break;
            }
            case Buy_Nutrition: {
                this._currentMenu = Enum.Menu.Buy_Food;
                break;
            }
            case Sell_Nutrition: {
                this._currentMenu = Enum.Menu.Sell_Food;
                break;
            }
            case Med_Nutrition: {
                this._currentMenu = Enum.Menu.Use_Med_Food;
                break;
            }
            case Use_Nutrition: {
                this._currentMenu = Enum.Menu.Use_Food;
                break;
            }
            case Data_Nutrition: {
                this._currentMenu = Enum.Menu.Data_Hunger;
                break;
            }
            case Registration_Prelim_Details: {
                digimon.getTournament().setCurrentTrophy(this._view.getCurrentSelectedTrophy(digimon));
                this._currentMenu = Enum.Menu.Tourney_Registration;
                break;
            }
            case Records_Prelim_Details: {
                Trophy t = digimon.getTournament().getTrophy(this._view.getTrophyInSchedule());
                this._model.getDigimon().getTournament().setCurrentTrophy(t);
                this._currentMenu = Enum.Menu.TrophyDetails;
                break;
            }
            case TrophyPrizeBits: {
                this._currentMenu = Enum.Menu.Tourney_Enter;
                break;
            }
            case TrophyPrizeItem: {
                this._currentMenu = Enum.Menu.TrophyPrizeBits;
                break;
            }
            case EvolSilhouette: {
                this._currentMenu = Enum.Menu.None;
                this._view.setCurrentAnim(null);
                this._model.getDigimon().forceState(Enum.State.EvolSilhouetteBack);
                break;
            }
            case DNA_Detail: {
                this._currentMenu = Enum.Menu.DNA_Inventory;
                break;
            }
            case DNA_GenerateValidate: {
                this._currentMenu = Enum.Menu.DNA_Validation;
                break;
            }
            case Medical: {
                this._currentMenu = Enum.Menu.None;
                this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
                break;
            }
            case DNA_Validation: {
                this._currentMenu = Enum.Menu.EvolutionMenu;
                break;
            }
            case EvolutionInventory: {
                this._currentMenu = Enum.Menu.EvolutionMenu;
                break;
            }
            case EvolutionState: {
                this._currentMenu = Enum.Menu.EvolutionMenu;
                this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
                break;
            }
            case UseEvolutionItem: {
                this._currentMenu = Enum.Menu.EvolutionInventory;
                break;
            }
            case DNA_Stats: 
            case DNA_Inventory: {
                this._currentMenu = Enum.Menu.DNA_Validation;
                break;
            }
            case Habitat_Description: {
                this._currentMenu = Enum.Menu.Habitat_Inventory;
                break;
            }
            case Habitat_Compatibility: {
                this._currentMenu = Enum.Menu.Habitat_Description;
                break;
            }
            case Habitat_Incompatibility: {
                this._currentMenu = Enum.Menu.Habitat_Compatibility;
                this._view.setConsumablePage(this._view.getCurrentFieldElement(this._currentMenu));
                break;
            }
            case Habitat_Shop_Description: {
                this._currentMenu = Enum.Menu.Habitat_Shop;
                break;
            }
            case Start: 
            case Settings: 
            case EvolutionTree: 
            case Set_EggClock: 
            case Save_Name: 
            case Load_Name: 
            case Host_Name_Battle: 
            case Host_Name_Jogress: {
                this.onClose();
                break;
            }
            case Habitat_Shop: {
                this._currentMenu = Enum.Menu.Shop_Validation;
                break;
            }
            case Item_Buy_Sell_Validation: {
                this._currentMenu = Enum.Menu.Shop_Validation;
                break;
            }
            case Item_Shop: {
                if (digimon.getCanSell(false)) {
                    this._currentMenu = Enum.Menu.Item_Buy_Sell_Validation;
                    break;
                }
                this._currentMenu = Enum.Menu.Shop_Validation;
                break;
            }
            case Habitat_Inventory: 
            case Item_Inventory: {
                this._currentMenu = Enum.Menu.Inventory_Validation;
                break;
            }
            case Shop_Validation: 
            case Inventory_Validation: {
                this._currentMenu = Enum.Menu.PraiseScold_Validation;
                this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
                break;
            }
            case Data_HealthTrack: {
                this._currentMenu = Enum.Menu.Data_HP;
                break;
            }
            case Data_Temp: {
                this._view.setTempDrag(false);
                this._currentMenu = Enum.Menu.None;
                break;
            }
            case Attack_Description: {
                if (this._battle != null && this._battle.getBattleType() != Battle.BattleType.None && this._battle.getInProgress()) {
                    this._currentMenu = Enum.Menu.AttackType_Validation;
                    break;
                }
                this._currentMenu = Enum.Menu.Data_Power;
                break;
            }
            case Attack_Validation: {
                break;
            }
            case EnemyAttack_Description: {
                this._currentMenu = Enum.Menu.Enemy_Attacks;
                break;
            }
            case Enemy_Attacks: {
                this._currentMenu = Enum.Menu.AttackType_Validation;
                break;
            }
            case Food_Purchase: {
                this._currentMenu = Enum.Menu.Buy_Food;
                break;
            }
            case Item_Purchase: {
                this._currentMenu = Enum.Menu.Buy_Item;
                break;
            }
            case Habitat_Purchase: {
                this._currentMenu = Enum.Menu.Habitat_Shop_Incompatibility;
                this._view.setConsumablePage(this._view.getCurrentFieldElement(this._currentMenu));
                this._view.getBackgroundAnim().checkBackNoAnim(digimon, this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle, this._view.getHabitat());
                break;
            }
            case Habitat_Shop_Incompatibility: {
                this._currentMenu = Enum.Menu.Habitat_Shop_Compatibility;
                this._view.setConsumablePage(this._view.getCurrentFieldElement(this._currentMenu));
                break;
            }
            case Habitat_Shop_Compatibility: {
                this._currentMenu = Enum.Menu.Habitat_Shop_Description;
                break;
            }
            case Food_Buy_Sell_Validation: {
                this._currentMenu = Enum.Menu.Feed_Validation;
                this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
                break;
            }
            case Food_Shop: {
                if (digimon.getCanSell(true)) {
                    this._currentMenu = Enum.Menu.Food_Buy_Sell_Validation;
                    break;
                }
                this._currentMenu = Enum.Menu.Feed_Validation;
                this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
                break;
            }
            case Use_Med_Food: {
                this._currentMenu = Enum.Menu.Medical;
                break;
            }
            case Use_Med_Item: {
                this._currentMenu = Enum.Menu.Medical;
                break;
            }
            case Use_Food: {
                this._currentMenu = Enum.Menu.Food_Inventory;
                break;
            }
            case Use_Item: {
                this._currentMenu = Enum.Menu.Item_Inventory;
                break;
            }
            case Buy_Food: {
                this._currentMenu = Enum.Menu.Food_Shop;
                break;
            }
            case Buy_Item: {
                this._currentMenu = Enum.Menu.Item_Shop;
                break;
            }
            case Food_Inventory: {
                this._currentMenu = Enum.Menu.Feed_Validation;
                break;
            }
            case Food_Inventory_Sell: {
                this._currentMenu = Enum.Menu.Food_Buy_Sell_Validation;
                break;
            }
            case Item_Inventory_Sell: {
                this._currentMenu = Enum.Menu.Item_Buy_Sell_Validation;
                break;
            }
            case Sell_Food: {
                this._currentMenu = Enum.Menu.Food_Inventory_Sell;
                break;
            }
            case Food_Sale: {
                this._currentMenu = Enum.Menu.Sell_Food;
                break;
            }
            case Item_Sale: {
                this._currentMenu = Enum.Menu.Sell_Item;
                break;
            }
            case Sell_Item: {
                this._currentMenu = Enum.Menu.Item_Inventory_Sell;
                break;
            }
            case Tourney_Enter: {
                this._currentMenu = Enum.Menu.Tourney_Options;
                break;
            }
            case Tourney_Registration: {
                this._currentMenu = Enum.Menu.Tourney_Enter;
                break;
            }
            case Tourney_Surrender: {
                this._currentMenu = Enum.Menu.Roster;
                break;
            }
            case Roster: {
                this._currentMenu = Enum.Menu.Royale_Lineup;
                break;
            }
            case Royale_Lineup: {
                this._currentMenu = Enum.Menu.None;
                break;
            }
            case AttackType_Validation: {
                this._currentMenu = Enum.Menu.Attack_Validation;
                break;
            }
            case UseCard_Validation: {
                this._currentMenu = Enum.Menu.AttackType_Validation;
                break;
            }
            case Battle_VS: {
                this._currentMenu = Enum.Menu.Battle_Validation;
                break;
            }
            case Battle_Style: {
                this._currentMenu = Enum.Menu.Battle_Validation;
                break;
            }
            case Multi_Validation_Jogress: {
                this._currentMenu = Enum.Menu.Battle_Validation;
                break;
            }
            case Multi_Validation_Battle: {
                this._currentMenu = Enum.Menu.Battle_VS;
                break;
            }
            case Card_Options: {
                this._currentMenu = Enum.Menu.Battle_Validation;
                break;
            }
            case Card_Shop: {
                this._currentMenu = Enum.Menu.Card_Options;
                this._view.getBackgroundAnim().checkBackNoAnim(this._model.getDigimon(), this._currentMenu, (int)this._model.getSettings().getGameScale(), this._battle);
                break;
            }
            case Tourney_Options: {
                this._currentMenu = Enum.Menu.Battle_VS;
                break;
            }
            case Season_Records: {
                this._currentMenu = Enum.Menu.Tourney_Options;
                break;
            }
            case Spring_Records: 
            case Summer_Records: 
            case Fall_Records: 
            case Winter_Records: {
                this._view.setTrophyPage(0, Enum.Season.Spring);
                this._currentMenu = Enum.Menu.Season_Records;
                break;
            }
            case TrophyDetails: {
                switch (this._model.getDigimon().getTournament().getCurrentTrophy().getSeason()) {
                    case Spring: {
                        this._currentMenu = Enum.Menu.Spring_Records;
                        break;
                    }
                    case Summer: {
                        this._currentMenu = Enum.Menu.Summer_Records;
                        break;
                    }
                    case Fall: {
                        this._currentMenu = Enum.Menu.Fall_Records;
                        break;
                    }
                    case Winter: {
                        this._currentMenu = Enum.Menu.Winter_Records;
                    }
                }
                break;
            }
            case Steps: {
                this._currentMenu = Enum.Menu.ZoneDetail;
                break;
            }
            case ZoneDetail: {
                this._currentMenu = Enum.Menu.MapZoneSelect;
                break;
            }
            case WorldMapSelect: {
                this._currentMenu = Enum.Menu.MapZoneSelect;
                break;
            }
            case WorldMapSelect_Ticket: {
                this._currentMenu = Enum.Menu.Use_Item;
                break;
            }
            case Map_Validation: {
                this._currentMenu = Enum.Menu.WorldMapSelect;
                break;
            }
            case Map_Validation_Ticket: {
                this._currentMenu = Enum.Menu.WorldMapSelect_Ticket;
                break;
            }
            case Zone_Validation: {
                this._currentMenu = Enum.Menu.MapZoneSelect;
                break;
            }
            case Zone_Validation_Ticket: {
                this._currentMenu = Enum.Menu.ChooseZone;
                break;
            }
            case MapZoneSelect: {
                this._currentMenu = Enum.Menu.None;
                if (digimon.getWorld().getTravelSpeed() == 0) break;
                digimon.disturb();
                digimon.canTravel();
                break;
            }
            case Set_AutoCare: {
                this._currentMenu = Enum.Menu.PraiseScold_Validation;
                break;
            }
            case Set_Clock: {
                this.setTimeFromString();
                if (this._model.getTime().timeChanged()) {
                    this._currentMenu = Enum.Menu.Clock_Validation;
                    break;
                }
                this._currentMenu = Enum.Menu.None;
                break;
            }
            default: {
                if (this._model.getDigimon().getCurrentState().equals((Object)Enum.State.ZoneChange)) break;
                this._currentMenu = Enum.Menu.None;
            }
        }
        switch (this._model.getDigimon().getCurrentState()) {
            case Virus_Training: 
            case Vaccine_Training: 
            case Data_Training: {
                this._currentMenu = Enum.Menu.Training_Select;
                this._view.endAnim();
                this._view.setSpriteCharDefault();
                this._view.setCurrentAnim(Enum.State.Idling);
            }
        }
        if (this._currentMenu == Enum.Menu.None) {
            this._view.setFrame(0);
        }
    }

    private void setTimeFromString() {
        String[] time = this._view.getTimeFromPanel().split(":");
        this._model.getTime().setHours(Byte.parseByte(time[0]), this._model.getDigimon());
        this._model.getTime().setMinutes(Byte.parseByte(time[1]), this._model.getDigimon());
    }
}

