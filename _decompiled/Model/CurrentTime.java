/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Model.Config;
import Model.Enum;
import Model.MinLapsePacket;
import Model.PhysicalState;

public class CurrentTime {
    private long _nanoRemainder;
    private boolean _canResetClockSpeed = true;
    private byte _seconds;
    private byte _minutes;
    private byte _hours = (byte)12;
    private int _fastMod = 1;
    private int _playerSetClockMod = 1;
    private int _timeChanged;
    private int _minutesBeforeChange = -1;
    private int _alarmMinutes = -1;

    public long getSecondEquivalent() {
        return 1000000000 / this.getClockSpeed();
    }

    public int getClockSpeed() {
        switch (this._fastMod) {
            case 2: {
                return Config._secondClockSpeed;
            }
            case 3: {
                return Config._thirdClockSpeed;
            }
            case 4: {
                return Config._fourthClockSpeed;
            }
        }
        return Config._firstClockSpeed;
    }

    public boolean canResetClockSpeed() {
        return this._canResetClockSpeed;
    }

    public void setCanResetClockSpeed(boolean b) {
        this._canResetClockSpeed = b;
    }

    public void setNanoRemainder(long newRemainder, boolean isPlaying, PhysicalState digimon) {
        this._nanoRemainder = newRemainder;
        long secondEquivalent = this.getSecondEquivalent();
        while (this._nanoRemainder >= secondEquivalent) {
            this.setSeconds((byte)(this._seconds + 1), isPlaying, digimon);
            this._nanoRemainder -= secondEquivalent;
        }
    }

    public long getNanoRemainder() {
        return this._nanoRemainder;
    }

    public byte getSeconds() {
        return this._seconds;
    }

    public MinLapsePacket setSeconds(byte newSeconds, boolean isPlaying, PhysicalState _myDigimon) {
        MinLapsePacket f = null;
        if (newSeconds > 0) {
            if (isPlaying && Math.abs(newSeconds - this._seconds) == 1) {
                _myDigimon.setLapsedLife(_myDigimon.getLapsedLife() + 1L);
                _myDigimon.secLapse(this._seconds);
            }
            this._seconds = newSeconds;
        }
        if (this._seconds >= Config._secondsMinute) {
            this._seconds = 0;
            this.setMinutes((byte)(this._minutes + 1), _myDigimon);
            if (isPlaying && this._minutes == 0 && this._hours == _myDigimon.getTournament().getTourneyTime(_myDigimon.getTrophyIndexInSchedule(_myDigimon.getTourneyAlarm()))) {
                _myDigimon.setTourneyAlarm(-1);
                _myDigimon.setCurrentState(Enum.State.TournamentAlert);
            }
            if (isPlaying) {
                this.setTimeChanged(this._timeChanged - 1);
            }
            if (isPlaying && _myDigimon.getAlive()) {
                f = _myDigimon.minLapse(this._minutes);
            }
        }
        return f;
    }

    public void setRawSeconds(byte newSecond) {
        this._seconds = newSecond;
    }

    public byte getMinutes() {
        return this._minutes;
    }

    public void setMinutes(byte newMinutes, PhysicalState digimon) {
        this._minutes = newMinutes;
        if (this._minutes >= Config._minutesHour) {
            this._minutes = 0;
            this.setHours((byte)(this._hours + 1), digimon);
        }
        if (this._minutes < 0) {
            this._minutes = (byte)59;
        }
    }

    public byte getHours() {
        return this._hours;
    }

    public void setHours(byte newHours, PhysicalState digimon) {
        this._hours = newHours;
        if (this._hours >= Config._hoursDay) {
            Enum.Season old = digimon.getSeason();
            digimon.dailyChange();
            digimon.setDay(digimon.getDay() + 1);
            Enum.Season s = digimon.getSeason();
            if (s != old) {
                digimon.seasonChange(old);
            }
            this._hours = 0;
        }
        if (this._hours < 0) {
            this._hours = (byte)(Config._hoursDay - 1);
        }
    }

    public void setMinuteBeforeChange(int b) {
        this._minutesBeforeChange = b;
    }

    public int getMinuteBeforeChange() {
        return this._minutesBeforeChange;
    }

    public void setTimeChanged(int b) {
        if (b >= 0) {
            this._timeChanged = b;
            if (this._timeChanged <= 0) {
                this._minutesBeforeChange = -1;
            }
        }
    }

    public int getTimeChanged() {
        return this._timeChanged;
    }

    public int getFastMod() {
        return this._fastMod;
    }

    public void setFastMod(int m, boolean forced) {
        this._fastMod = m;
        if (forced) {
            this._playerSetClockMod = m;
        }
    }

    public void setFastMod(int newMod) {
        this.setFastMod(newMod, false);
    }

    public void clockSpeedToPlayerSetting() {
        this._fastMod = this._playerSetClockMod;
    }

    public void setAlarmMinutes(int m) {
        this._alarmMinutes = m;
    }

    public int getAlarmMinutes() {
        return this._alarmMinutes;
    }

    public boolean checkCheating(PhysicalState digimon) {
        if (this.timeChanged() && this._timeChanged > 0) {
            this._timeChanged = 0;
            this._minutesBeforeChange = -1;
            digimon.setGameModified(true);
            return true;
        }
        if (this._minutesBeforeChange >= 0 && this.timeChanged()) {
            this._timeChanged = 1440;
            return false;
        }
        return false;
    }

    public boolean timeChanged() {
        return Math.abs(this._minutesBeforeChange - this.getTotalMinutesOfDay()) >= 1;
    }

    public int getTotalMinutesOfDay() {
        return this.getTotalMinutesOfDay(this._hours, this._minutes);
    }

    public int getTotalMinutesOfDay(int hour, int min) {
        return hour * Config._minutesHour + min;
    }

    public void resetTime() {
        byte[] time = this.getTimeFromMinutes(this._minutesBeforeChange);
        this._hours = time[0];
        this._minutes = time[1];
    }

    public byte[] getTimeFromMinutes(int minutes) {
        return new byte[]{(byte)(minutes / Config._minutesHour), (byte)(minutes % Config._minutesHour)};
    }

    public void checkSleepAlarm(int hour, int min) {
        if (this.getTotalMinutesOfDay(hour, min) == this._alarmMinutes) {
            // empty if block
        }
    }

    public void checkSleepAlarm(int totalMinutesOfDay) {
        if (totalMinutesOfDay == this._alarmMinutes) {
            // empty if block
        }
    }

    public void turnOffAlarm() {
        this._alarmMinutes = -1;
    }
}

