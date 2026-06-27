/*
 * Decompiled with CFR 0.152.
 */
import Controller.ClockTic;
import Model.Controller;
import Model.CrashEntry;
import Model.CurrentTime;
import Model.PhysicalState;
import Model.ViewSettings;
import View.KeyboardCursor;
import View.SoundConfig;
import View.SoundObj;
import View.SpriteAnim;
import View.ViewConfig;
import java.io.File;

public class vpetSettings {
    private ClockTic _controller;
    private final boolean IS_TOURNAMENT_VERSION = false;

    public vpetSettings() {
        String MOD_FOLDER = "files" + File.separator + "mods" + File.separator;
        String RESOURCES_FOLDER = "/resources/";
        SoundConfig.loadConfig(MOD_FOLDER);
        ViewConfig.loadConfig(MOD_FOLDER);
        PhysicalState digimon = new PhysicalState(MOD_FOLDER, "/Model/", false);
        CurrentTime time = new CurrentTime();
        digimon.setClock(time);
        ViewSettings settings = new ViewSettings();
        settings.loadSettings();
        digimon.setSettings(settings);
        Controller model = new Controller(time, digimon, settings);
        SoundObj sounds = new SoundObj(MOD_FOLDER, RESOURCES_FOLDER, settings);
        SpriteAnim view = new SpriteAnim(sounds, MOD_FOLDER, RESOURCES_FOLDER);
        view.setAlwaysOnTop(settings.isOnTop());
        this._controller = new ClockTic(view, model, sounds, false, MOD_FOLDER);
        KeyboardCursor keyboard = new KeyboardCursor(this._controller, view, sounds);
        view.setKeyboard(keyboard);
        this._controller.setKeyboard(keyboard);
    }

    public static void main(String[] args) {
        Thread.setDefaultUncaughtExceptionHandler(new Thread.UncaughtExceptionHandler(){

            @Override
            public void uncaughtException(Thread t, Throwable e) {
                CrashEntry crash = new CrashEntry();
                CrashEntry.generateEntry(e);
                e.printStackTrace();
            }
        });
        vpetSettings vPet = new vpetSettings();
        vPet._controller.gameLoop();
    }
}

