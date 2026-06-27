/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Controller.Utility;
import Model.Config;
import Model.DNA;
import Model.Enum;
import Model.EvolutionInfo;
import Model.Habitat;
import Model.PhysicalState;
import Model.Taste;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.util.AbstractMap;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.Map;
import java.util.Random;

public class Evolution {
    private ArrayList<EvolutionInfo> _evolDigimon;
    private boolean _dna;
    private final String MOD_FOLDER;
    private final String MODEL_FOLDER;

    public ArrayList<EvolutionInfo> getEvolDigimon() {
        return this._evolDigimon;
    }

    public boolean getDNA() {
        if (this._dna) {
            this._dna = false;
            return true;
        }
        return false;
    }

    public Evolution(String modFolder, String modelFolder) {
        this.MOD_FOLDER = modFolder;
        this.MODEL_FOLDER = modelFolder;
        this.initEvolDigimon();
    }

    public boolean checkEvolReq(PhysicalState digimon, EvolutionInfo evol, boolean connecting, int probChange) {
        boolean success = false;
        this._dna = Config._enableDNAReqReplacement ? (this.hasDNARequirement(evol, digimon) ? this.testDNA(evol, digimon) : false) : false;
        int total = digimon.getVaccinePower() + digimon.getDataPower() + digimon.getVirusPower();
        try {
            int winRate = (int)((double)digimon.getWins() / (double)digimon.getBattles() * 100.0);
            if (evol != null && (Config._jogressOptional || evol.getSpecialEvol() != Enum.SpecialEvolution.Jogress || evol.getSpecialEvol() == Enum.SpecialEvolution.Jogress && connecting) && (Config._fusionOptional || evol.getSpecialEvol() != Enum.SpecialEvolution.Fusion || evol.getSpecialEvol() == Enum.SpecialEvolution.Fusion && connecting) && this.checkStatTotal(digimon, evol) && (this.testEvol(evol.getBattles(), digimon.getBattles()) || this.getDNA()) && (this.testAttribute(evol.getDataPower()[0], digimon.getDataPower(), total) || this.getDNA()) && (this.testAttribute(evol.getDataPower()[1], digimon.getDataPower(), total) || this.getDNA()) && (this.testAttribute(evol.getVaccinePower()[0], digimon.getVaccinePower(), total) || this.getDNA()) && (this.testAttribute(evol.getVaccinePower()[1], digimon.getVaccinePower(), total) || this.getDNA()) && (this.testAttribute(evol.getVirusPower()[0], digimon.getVirusPower(), total) || this.getDNA()) && (this.testAttribute(evol.getVirusPower()[1], digimon.getVirusPower(), total) || this.getDNA()) && (evol.getTime().equals((Object)Enum.Time.None) || evol.getTime().equals((Object)digimon.getTrainTime()) || this.getDNA()) && (evol.getWeight() == Enum.Weight.None || this.checkWeightReq(digimon, evol) || this.getDNA()) && (this.testEvol(evol.getDisturb(), digimon.getDisturb()) || this.getDNA()) && (this.testEvol(evol.getOvereat(), digimon.getOvereat()) || this.getDNA()) && (this.testEvol(evol.getSick(), digimon.getSickCount()) || this.getDNA()) && (this.testEvol(evol.getInjured(), digimon.getInjCount()) || this.getDNA()) && (evol.getMood() == Enum.Mood.None || this.checkMoodReq(digimon, evol) || this.getDNA()) && (this.checkObedienceReq(digimon, evol) || this.getDNA()) && (this.checkTempReq(digimon, evol) || this.getDNA()) && (this.testEvol(evol.getWins(), winRate) || this.getDNA()) && (this.testEvol(evol.getMistakes(), digimon.getMistake()) || this.getDNA()) && (evol.getMajorFood().equals((Object)Enum.Food.None) || evol.getMajorFood() == digimon.getMajorFood() || this.getDNA()) && (this.testEvol(evol.getIncarnations(), digimon.getGenerationHistory().size()) || this.getDNA()) && (evol.getLevelFought() == 0 || this.testEvol(evol.getLevelFoughtCondition(), digimon.getLevelFought(evol.getLevelFought())) || this.getDNA()) && (evol.getXAntibody() != Enum.XAntibody.Induced || digimon.getXAntibodyState() != Enum.XAntibodyState.None || Config._dnaSkipsXAntibodyReq && this.getDNA()) && (evol.getHabitat() == -1 || this.checkHabitatReq(digimon, evol) || this.getDNA())) {
                Random r;
                int i;
                int prob = evol.getProb() + probChange + digimon.getBonus() + (int)((double)winRate * Config._winRateEvolProbabilityIncCoefficient);
                success = prob < evol.getProbBound() ? prob > (i = (r = new Random()).nextInt(evol.getProbBound())) : true;
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        return success;
    }

    public boolean checkHabitatReq(PhysicalState digimon, EvolutionInfo evol) {
        return Config._enableTimerBasedRequirements ? evol.getHabitat() == digimon.getMajorHabitat() : evol.getHabitat() == digimon.getCurrentHabitatIndex();
    }

    public boolean checkTempReq(PhysicalState digimon, EvolutionInfo evol) {
        return Config._enableTimerBasedRequirements ? this.checkTemp(digimon.getTempRecord(), evol.getTempReq()) : this.checkTemp(new int[]{1, digimon.getTemp()}, evol.getTempReq());
    }

    public boolean checkWeightReq(PhysicalState digimon, EvolutionInfo evol) {
        return evol.getWeight().equals((Object)(Config._enableTimerBasedRequirements ? digimon.getMajorWeight() : digimon.getOverweight()));
    }

    public boolean checkMoodReq(PhysicalState digimon, EvolutionInfo evol) {
        return evol.getMood() == (Config._enableTimerBasedRequirements ? digimon.getMajorMood(digimon.getMoodRecord()) : digimon.getCurrentMood());
    }

    public boolean checkObedienceReq(PhysicalState digimon, EvolutionInfo evol) {
        return Config._enableTimerBasedRequirements ? this.checkAverage(digimon.getObedienceRecord(), evol.getObedience().getValue(), evol.getObedience().getKey()) : this.testEvol(evol.getObedience(), digimon.getObedience());
    }

    private boolean checkStatTotal(PhysicalState digimon, EvolutionInfo evol) {
        int evolTotal = 0;
        int digimonTotal = digimon.getVaccinePower() + digimon.getDataPower() + digimon.getVirusPower();
        switch (evol.getVaccinePower()[0].getKey()) {
            case GreaterThan: 
            case EqualTo: {
                evolTotal = (int)((double)evolTotal + (evol.getVaccinePower()[0].getValue() + (double)(evol.getVaccinePower()[0].getKey() == Enum.Condition.GreaterThan ? 1 : 0)));
            }
        }
        switch (evol.getDataPower()[0].getKey()) {
            case GreaterThan: 
            case EqualTo: {
                evolTotal = (int)((double)evolTotal + (evol.getDataPower()[0].getValue() + (double)(evol.getDataPower()[0].getKey() == Enum.Condition.GreaterThan ? 1 : 0)));
            }
        }
        switch (evol.getVirusPower()[0].getKey()) {
            case GreaterThan: 
            case EqualTo: {
                evolTotal = (int)((double)evolTotal + (evol.getVirusPower()[0].getValue() + (double)(evol.getVirusPower()[0].getKey() == Enum.Condition.GreaterThan ? 1 : 0)));
            }
        }
        return evolTotal <= digimonTotal;
    }

    public boolean checkTemp(int[] record, byte[] temp) {
        boolean valid = false;
        double average = (double)record[1] / (double)record[0];
        valid = temp[0] < temp[1] ? average >= (double)temp[0] && average <= (double)temp[1] : true;
        return valid;
    }

    public boolean checkAverage(int[] record, int req, Enum.Condition c) {
        boolean valid = false;
        double average = (double)record[1] / ((double)record[0] == 0.0 ? 1.0 : (double)record[0]);
        double goal = req;
        if (c == Enum.Condition.None) {
            valid = true;
        } else {
            switch (c) {
                case GreaterThan: {
                    valid = average > goal;
                    break;
                }
                case LessThan: {
                    valid = average < goal;
                    break;
                }
                case EqualTo: {
                    valid = average == goal;
                }
            }
        }
        return valid;
    }

    private boolean testCondition(Enum.Condition condition, double first, double second) {
        switch (condition) {
            case LessThan: {
                return this.lessThan(first, second);
            }
            case EqualTo: {
                return this.equalTo(first, second);
            }
            case GreaterThan: {
                return this.greaterThan(first, second);
            }
        }
        return false;
    }

    public boolean testAttribute(Map.Entry<Enum.Condition, Double> entry, int second, int total) {
        Enum.Condition condition = entry.getKey();
        double first = entry.getValue();
        boolean pass = true;
        if (first < 1.0 && first > 0.0) {
            if (condition != Enum.Condition.None && total > 0) {
                double p = (double)second / (double)total;
                pass = this.testCondition(condition, first, p);
            } else {
                pass = false;
            }
        } else {
            AbstractMap.SimpleEntry<Enum.Condition, Integer> e = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(condition, (int)first);
            pass = this.testEvol(e, second);
        }
        return pass;
    }

    public boolean testEvol(Map.Entry<Enum.Condition, Integer> entry, int second) {
        Enum.Condition condition = entry.getKey();
        int first = entry.getValue();
        boolean pass = true;
        if (condition != Enum.Condition.None) {
            pass = this.testCondition(condition, first, second);
        }
        return pass;
    }

    private boolean greaterThan(double first, double second) {
        return second > first;
    }

    private boolean lessThan(double first, double second) {
        return second < first;
    }

    private boolean equalTo(double first, double second) {
        return first == second;
    }

    private boolean checkSpecialCondition(Enum.SpecialEvolution condition, int itemID, int evolItemID, int foodID, int evolFoodID, PhysicalState digimon, boolean dying, boolean modeChange) {
        boolean valid = false;
        switch (condition) {
            case None: 
            case Jogress: 
            case Fusion: 
            case Failed: {
                if (evolItemID != -1) {
                    if (itemID == -1 || itemID != evolItemID) break;
                    valid = true;
                    break;
                }
                if (evolFoodID != -1) {
                    if (foodID == -1 || foodID != evolFoodID) break;
                    valid = true;
                    break;
                }
                if (itemID >= 0 || foodID >= 0) break;
                valid = !dying && !modeChange;
                break;
            }
            case Death: {
                valid = dying;
                break;
            }
            case Xros: {
                break;
            }
            case Mode: {
                valid = modeChange;
            }
        }
        return valid;
    }

    private boolean checkEvol(PhysicalState digimon, EvolutionInfo newEvol, ArrayList<EvolutionInfo> evolDigimon, int item, int food, boolean dying, boolean modeChange, int probChange) {
        ArrayList<EvolutionInfo> finalEvolution = this.getValidEvolutionFromList(digimon, newEvol, evolDigimon, item, food, dying, modeChange, probChange);
        if (finalEvolution != null && finalEvolution.size() > 0) {
            Random r = new Random();
            this.digivolve(finalEvolution.get(r.nextInt(finalEvolution.size())), digimon, evolDigimon, false, -1);
            return true;
        }
        return false;
    }

    public ArrayList<EvolutionInfo> getValidEvolutionFromList(PhysicalState digimon, EvolutionInfo newEvol, ArrayList<EvolutionInfo> evolDigimon, int item, int food, boolean dying, boolean modeChange, int probChange) {
        ArrayList<EvolutionInfo> evolutions = this.getValidEvolutions(digimon, newEvol, false, item, food, dying, modeChange, probChange);
        return this.getFinalEvolution(evolutions, digimon);
    }

    public ArrayList<EvolutionInfo> getFinalEvolution(ArrayList<EvolutionInfo> evolutions, PhysicalState digimon) {
        ArrayList<EvolutionInfo> tiedEvos = this.getTiedEvolutions(evolutions, digimon);
        if (tiedEvos.size() > 1) {
            tiedEvos = this.tieBreaker(tiedEvos, digimon);
        }
        return tiedEvos;
    }

    private ArrayList<EvolutionInfo> getTiedEvolutions(ArrayList<EvolutionInfo> evolutions, PhysicalState digimon) {
        ArrayList<EvolutionInfo> tiedEvolutions = new ArrayList<EvolutionInfo>();
        double currentRecord = -999.0;
        for (EvolutionInfo evol : evolutions) {
            double fulfilledReq = this.getFulfilledReq(evol, digimon);
            if (!(fulfilledReq >= currentRecord)) continue;
            if (fulfilledReq > currentRecord) {
                tiedEvolutions.clear();
            }
            tiedEvolutions.add(evol);
            currentRecord = fulfilledReq;
        }
        return tiedEvolutions;
    }

    private ArrayList<EvolutionInfo> tieBreaker(ArrayList<EvolutionInfo> evolutions, PhysicalState digimon) {
        ArrayList<EvolutionInfo> finalTies = new ArrayList<EvolutionInfo>();
        if (evolutions.size() > 1) {
            int currentDeviation = this.calcDeviation(evolutions.get(0), digimon);
            for (EvolutionInfo e : evolutions) {
                int deviation = this.calcDeviation(e, digimon);
                if (deviation > currentDeviation) continue;
                if (deviation < currentDeviation) {
                    finalTies.clear();
                }
                finalTies.add(e);
                currentDeviation = deviation;
            }
        } else if (evolutions.size() == 1) {
            finalTies.add(evolutions.get(0));
        }
        return finalTies;
    }

    private int calcDeviation(EvolutionInfo evol, PhysicalState digimon) {
        int deviation = 0;
        int total = digimon.getVaccinePower() + digimon.getDataPower() + digimon.getVirusPower();
        if (this.testEvol(evol.getBattles(), digimon.getBattles())) {
            deviation += Math.abs(evol.getBattles().getValue() - digimon.getBattles());
        }
        if (this.testAttribute(evol.getDataPower()[0], digimon.getDataPower(), total)) {
            deviation = (int)((double)deviation + Math.abs(evol.getDataPower()[0].getValue() - (double)digimon.getDataPower()));
        }
        if (this.testAttribute(evol.getDataPower()[1], digimon.getDataPower(), total)) {
            deviation = (int)((double)deviation + Math.abs(evol.getDataPower()[1].getValue() - (double)digimon.getDataPower()));
        }
        if (this.testAttribute(evol.getVaccinePower()[0], digimon.getVaccinePower(), total)) {
            deviation = (int)((double)deviation + Math.abs(evol.getVaccinePower()[0].getValue() - (double)digimon.getVaccinePower()));
        }
        if (this.testAttribute(evol.getVaccinePower()[1], digimon.getVaccinePower(), total)) {
            deviation = (int)((double)deviation + Math.abs(evol.getVaccinePower()[1].getValue() - (double)digimon.getVaccinePower()));
        }
        if (this.testAttribute(evol.getVirusPower()[0], digimon.getVirusPower(), total)) {
            deviation = (int)((double)deviation + Math.abs(evol.getVirusPower()[0].getValue() - (double)digimon.getVirusPower()));
        }
        if (this.testAttribute(evol.getVirusPower()[1], digimon.getVirusPower(), total)) {
            deviation = (int)((double)deviation + Math.abs(evol.getVirusPower()[1].getValue() - (double)digimon.getVirusPower()));
        }
        if (this.testEvol(evol.getDisturb(), digimon.getDisturb())) {
            deviation += Math.abs(evol.getDisturb().getValue() - digimon.getDisturb());
        }
        if (this.testEvol(evol.getOvereat(), digimon.getOvereat())) {
            deviation += Math.abs(evol.getOvereat().getValue() - digimon.getOvereat());
        }
        if (this.testEvol(evol.getSick(), digimon.getSickCount())) {
            deviation += Math.abs(evol.getSick().getValue() - digimon.getSickCount());
        }
        if (this.testEvol(evol.getInjured(), digimon.getInjCount())) {
            deviation += Math.abs(evol.getInjured().getValue() - digimon.getInjCount());
        }
        if (this.testEvol(evol.getWins(), (int)((double)digimon.getWins() / (double)digimon.getBattles() * 100.0))) {
            deviation += Math.abs(evol.getWins().getValue() - (int)((double)digimon.getWins() / (double)digimon.getBattles() * 100.0));
        }
        if (this.testEvol(evol.getMistakes(), digimon.getMistake())) {
            deviation += Math.abs(evol.getMistakes().getValue() - digimon.getMistake());
        }
        return deviation;
    }

    public double getFulfilledReq(EvolutionInfo evol, PhysicalState digimon) {
        double requirements = 1.0 + evol.getPriority();
        EvolutionInfo current = this.getDigimon(digimon.getIndex());
        int total = digimon.getVaccinePower() + digimon.getDataPower() + digimon.getVirusPower();
        if (evol.getBattles().getKey() != Enum.Condition.None && this.testEvol(evol.getBattles(), digimon.getBattles())) {
            requirements += (double)Config._battleRate;
        }
        if (evol.getDataPower()[0].getKey() != Enum.Condition.None && this.testAttribute(evol.getDataPower()[0], digimon.getDataPower(), total)) {
            requirements += (double)Config._dataRate * this.scaleRate(evol.getDataPower()[0].getKey(), evol.getDataPower()[0].getValue(), current.getDataPower()[0].getValue());
        }
        if (evol.getDataPower()[1].getKey() != Enum.Condition.None && this.testAttribute(evol.getDataPower()[1], digimon.getDataPower(), total)) {
            requirements += (double)Config._dataRate * this.scaleRate(evol.getDataPower()[1].getKey(), evol.getDataPower()[1].getValue(), current.getDataPower()[1].getValue());
        }
        if (evol.getVaccinePower()[0].getKey() != Enum.Condition.None && this.testAttribute(evol.getVaccinePower()[0], digimon.getVaccinePower(), total)) {
            requirements += (double)Config._vaccineRate * this.scaleRate(evol.getVaccinePower()[0].getKey(), evol.getVaccinePower()[0].getValue(), current.getVaccinePower()[0].getValue());
        }
        if (evol.getVaccinePower()[1].getKey() != Enum.Condition.None && this.testAttribute(evol.getVaccinePower()[1], digimon.getVaccinePower(), total)) {
            requirements += (double)Config._vaccineRate * this.scaleRate(evol.getVaccinePower()[1].getKey(), evol.getVaccinePower()[1].getValue(), current.getVaccinePower()[1].getValue());
        }
        if (evol.getVirusPower()[0].getKey() != Enum.Condition.None && this.testAttribute(evol.getVirusPower()[0], digimon.getVirusPower(), total)) {
            requirements += (double)Config._virusRate * this.scaleRate(evol.getVirusPower()[0].getKey(), evol.getVirusPower()[0].getValue(), current.getVirusPower()[0].getValue());
        }
        if (evol.getVirusPower()[1].getKey() != Enum.Condition.None && this.testAttribute(evol.getVirusPower()[1], digimon.getVirusPower(), total)) {
            requirements += (double)Config._virusRate * this.scaleRate(evol.getVirusPower()[1].getKey(), evol.getVirusPower()[1].getValue(), current.getVirusPower()[1].getValue());
        }
        if (!evol.getTime().equals((Object)Enum.Time.None) && evol.getTime().equals((Object)digimon.getTrainTime())) {
            requirements += (double)Config._timeRate;
        }
        if (evol.getWeight() != Enum.Weight.None && this.checkWeightReq(digimon, evol)) {
            requirements += (double)Config._weightRate;
        }
        if (evol.getDisturb().getKey() != Enum.Condition.None && this.testEvol(evol.getDisturb(), digimon.getDisturb())) {
            requirements += (double)Config._disturbRate;
        }
        if (evol.getOvereat().getKey() != Enum.Condition.None && this.testEvol(evol.getOvereat(), digimon.getOvereat())) {
            requirements += (double)Config._overeatRate;
        }
        if (evol.getSick().getKey() != Enum.Condition.None && this.testEvol(evol.getSick(), digimon.getSickCount())) {
            requirements += (double)Config._sicknessRate;
        }
        if (evol.getInjured().getKey() != Enum.Condition.None && this.testEvol(evol.getInjured(), digimon.getInjCount())) {
            requirements += (double)Config._injuryRate;
        }
        if (evol.getMood() != Enum.Mood.None && this.checkMoodReq(digimon, evol)) {
            requirements += (double)Config._moodRate;
        }
        if (evol.getObedience().getKey() != Enum.Condition.None && this.checkObedienceReq(digimon, evol)) {
            requirements += (double)Config._obedienceRate;
        }
        if (evol.getTempReq()[1] != -1 && this.checkTempReq(digimon, evol)) {
            requirements += (double)Config._temperatureRate;
        }
        if (evol.getWins().getKey() != Enum.Condition.None && this.testEvol(evol.getWins(), (int)((double)digimon.getWins() / (double)digimon.getBattles() * 100.0))) {
            requirements += (double)Config._winRateRate;
        }
        if (evol.getMistakes().getKey() != Enum.Condition.None && this.testEvol(evol.getMistakes(), digimon.getMistake())) {
            switch (evol.getMistakes().getKey()) {
                case LessThan: {
                    requirements += (double)Config._careMistakeLessRate;
                    break;
                }
                case GreaterThan: {
                    requirements += (double)Config._careMistakeGreaterRate;
                    break;
                }
                case EqualTo: {
                    requirements += (double)Config._careMistakeEqualRate;
                    break;
                }
                default: {
                    requirements += (double)Config._careMistakeNoneRate;
                }
            }
        }
        if (evol.getLevelFought() != 0 && evol.getLevelFoughtCondition().getKey() != Enum.Condition.None && this.testEvol(evol.getLevelFoughtCondition(), digimon.getLevelFought(evol.getLevelFought()))) {
            requirements += (double)Config._levelFoughtRate;
        }
        if (evol.getIncarnations().getKey() != Enum.Condition.None && this.testEvol(evol.getIncarnations(), digimon.getGenerationHistory().size())) {
            requirements += (double)Config._reincarnationsRate;
        }
        if (evol.getMajorFood() != Enum.Food.None && evol.getMajorFood().equals((Object)digimon.getMajorFood())) {
            requirements += (double)Config._foodEatenRate;
        }
        if (evol.getXAntibody() == Enum.XAntibody.Induced && digimon.getXAntibodyState() != Enum.XAntibodyState.None) {
            requirements += (double)Config._xAntibodyRate;
        }
        int majorHabitat = digimon.getMajorHabitat();
        if (evol.getHabitat() != -1 && this.checkHabitatReq(digimon, evol)) {
            requirements += (double)Config._habitatRate;
        }
        Habitat h = majorHabitat >= 0 ? digimon.getHabitats().get(digimon.getMajorHabitat()) : null;
        int change = (digimon.compatibleElement(evol.getNewElement(), h) ? Config._compatibleElementPriorityChange : (byte)0) + (digimon.compatibleField(evol.getNewField(), h) ? Config._compatibleFieldPriorityChange : (byte)0) + (digimon.incompatibleField(evol.getNewField(), h) ? Config._incompatibleFieldPriorityChange : (byte)0) + (digimon.incompatibleElement(evol.getNewElement(), h) ? Config._incompatibleElementPriorityChange : (byte)0);
        return requirements + this.getDNAReq(evol, digimon) + (double)change;
    }

    public boolean testDNA(EvolutionInfo evol, PhysicalState digimon) {
        DNA dna = digimon.getDNA();
        return this.testEvol(evol.getVirusBuster(), dna.getPercent(Enum.Field.VirusBuster)) && this.testEvol(evol.getMetalEmpire(), dna.getPercent(Enum.Field.MetalEmpire)) && this.testEvol(evol.getDragonsRoar(), dna.getPercent(Enum.Field.DragonsRoar)) && this.testEvol(evol.getJungleTrooper(), dna.getPercent(Enum.Field.JungleTrooper)) && this.testEvol(evol.getDeepSea(), dna.getPercent(Enum.Field.DeepSaver)) && this.testEvol(evol.getNightmareSoldier(), dna.getPercent(Enum.Field.NightmareSoldier)) && this.testEvol(evol.getWindGuardian(), dna.getPercent(Enum.Field.WindGuardian)) && this.testEvol(evol.getNatureSpirit(), dna.getPercent(Enum.Field.NatureSpirit)) && this.testEvol(evol.getDarkArea(), dna.getPercent(Enum.Field.DarkArea)) && this.testEvol(evol.getNone(), dna.getPercent(Enum.Field.None));
    }

    public boolean hasDNARequirement(EvolutionInfo evol, PhysicalState digimon) {
        return !evol.getVirusBuster().getKey().equals((Object)Enum.Condition.None) || !evol.getMetalEmpire().getKey().equals((Object)Enum.Condition.None) || !evol.getDragonsRoar().getKey().equals((Object)Enum.Condition.None) || !evol.getJungleTrooper().getKey().equals((Object)Enum.Condition.None) || !evol.getDeepSea().getKey().equals((Object)Enum.Condition.None) || !evol.getNightmareSoldier().getKey().equals((Object)Enum.Condition.None) || !evol.getWindGuardian().getKey().equals((Object)Enum.Condition.None) || !evol.getNatureSpirit().getKey().equals((Object)Enum.Condition.None) || !evol.getDarkArea().getKey().equals((Object)Enum.Condition.None) || !evol.getNone().getKey().equals((Object)Enum.Condition.None);
    }

    private double getDNAReq(EvolutionInfo evol, PhysicalState digimon) {
        double requirements = 0.0;
        DNA dna = digimon.getDNA();
        if (evol.getVirusBuster().getKey() != Enum.Condition.None && this.testEvol(evol.getVirusBuster(), dna.getPercent(Enum.Field.VirusBuster))) {
            requirements += (double)Config._virusBusterRate;
        }
        if (evol.getMetalEmpire().getKey() != Enum.Condition.None && this.testEvol(evol.getMetalEmpire(), dna.getPercent(Enum.Field.MetalEmpire))) {
            requirements += (double)Config._metalEmpireRate;
        }
        if (evol.getDragonsRoar().getKey() != Enum.Condition.None && this.testEvol(evol.getDragonsRoar(), dna.getPercent(Enum.Field.DragonsRoar))) {
            requirements += (double)Config._dragonsRoarRate;
        }
        if (evol.getJungleTrooper().getKey() != Enum.Condition.None && this.testEvol(evol.getJungleTrooper(), dna.getPercent(Enum.Field.JungleTrooper))) {
            requirements += (double)Config._jungleTrooperRate;
        }
        if (evol.getDeepSea().getKey() != Enum.Condition.None && this.testEvol(evol.getDeepSea(), dna.getPercent(Enum.Field.DeepSaver))) {
            requirements += (double)Config._deepSeaRate;
        }
        if (evol.getNightmareSoldier().getKey() != Enum.Condition.None && this.testEvol(evol.getNightmareSoldier(), dna.getPercent(Enum.Field.NightmareSoldier))) {
            requirements += (double)Config._nightmareSoldierRate;
        }
        if (evol.getWindGuardian().getKey() != Enum.Condition.None && this.testEvol(evol.getWindGuardian(), dna.getPercent(Enum.Field.WindGuardian))) {
            requirements += (double)Config._windGuardianRate;
        }
        if (evol.getNatureSpirit().getKey() != Enum.Condition.None && this.testEvol(evol.getNatureSpirit(), dna.getPercent(Enum.Field.NatureSpirit))) {
            requirements += (double)Config._natureSpiritRate;
        }
        if (evol.getDarkArea().getKey() != Enum.Condition.None && this.testEvol(evol.getDarkArea(), dna.getPercent(Enum.Field.DarkArea))) {
            requirements += (double)Config._darkAreaRate;
        }
        if (evol.getNone().getKey() != Enum.Condition.None && this.testEvol(evol.getNone(), dna.getPercent(Enum.Field.None))) {
            requirements += (double)Config._noneRate;
        }
        if (this.hasDNARequirement(evol, digimon) && this.testDNA(evol, digimon)) {
            requirements += (double)Config._dnaFulfilledRate;
        }
        return requirements;
    }

    private double scaleRate(Enum.Condition condition, double first, double second) {
        switch (condition) {
            case GreaterThan: 
            case EqualTo: {
                if (first > second) {
                    return (first - second) / first;
                }
            }
            case LessThan: {
                if (!(second > first)) break;
                return (second - first) / second;
            }
        }
        return 1.0;
    }

    private ArrayList<EvolutionInfo> getValidEvolutions(PhysicalState digimon, EvolutionInfo newEvol, boolean connecting, int item, int food, boolean dying, boolean modeChange, int probChange) {
        ArrayList<EvolutionInfo> evolutions = new ArrayList<EvolutionInfo>();
        try {
            for (int i = 0; i < newEvol.getEvolutions().size(); ++i) {
                EvolutionInfo validEvol = null;
                validEvol = item != -1 && newEvol.getEvolutions().get(i).getEvolItemID() != -1 ? this.checkValidEvolution(newEvol.getEvolutions().get(i), digimon, item, food, connecting, dying, modeChange, probChange) : (food != -1 && newEvol.getEvolutions().get(i).getEvolFoodID() != -1 ? this.checkValidEvolution(newEvol.getEvolutions().get(i), digimon, item, food, connecting, dying, modeChange, probChange) : this.checkValidEvolution(newEvol.getEvolutions().get(i), digimon, item, food, connecting, dying, modeChange, probChange));
                if (validEvol == null) continue;
                evolutions.add(validEvol);
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        return evolutions;
    }

    private EvolutionInfo checkValidEvolution(EvolutionInfo evol, PhysicalState digimon, int item, int food, boolean connecting, boolean dying, boolean modeChange, int probChange) {
        EvolutionInfo newEvol = null;
        if (this.checkSpecialCondition(evol.getSpecialEvol(), item, evol.getEvolItemID(), food, evol.getEvolFoodID(), digimon, dying, modeChange) && this.checkEvolReq(digimon, evol, connecting, probChange)) {
            newEvol = evol;
        }
        return newEvol;
    }

    public String checkJogress(PhysicalState digimon, EvolutionInfo newEvol) {
        ArrayList<EvolutionInfo> evolutions = this.getValidEvolutions(digimon, newEvol, true, -1, -1, false, false, 0);
        String evols = "";
        if (evolutions.size() > 0) {
            for (EvolutionInfo e : evolutions) {
                switch (e.getSpecialEvol()) {
                    case Jogress: {
                        String partner = this.getPartnerAttribute(e.getNewAttribute(), digimon);
                        if (partner == "") break;
                        evols = evols + partner;
                        break;
                    }
                    case Fusion: {
                        evols = evols + e.getName() + ",";
                    }
                }
            }
        }
        return evols;
    }

    public EvolutionInfo pairJogressMatch(PhysicalState digimon, String jogressMatch) {
        ArrayList<EvolutionInfo> evolutions = this.getValidEvolutions(digimon, this.getDigimon(digimon.getIndex()), true, -1, -1, false, false, 0);
        ArrayList<EvolutionInfo> evol = new ArrayList<EvolutionInfo>();
        if (evolutions.size() > 0) {
            block6: for (EvolutionInfo evolutionInfo : evolutions) {
                switch (evolutionInfo.getSpecialEvol()) {
                    case Fusion: {
                        if (!evolutionInfo.getName().equals(jogressMatch)) break;
                        evol.add(evolutionInfo);
                        break;
                    }
                    case Jogress: {
                        try {
                            if (!this.getPartnerAttribute(evolutionInfo.getNewAttribute(), digimon).contains(jogressMatch)) continue block6;
                            evol.add(evolutionInfo);
                            break;
                        }
                        catch (IllegalArgumentException illegalArgumentException) {
                            // empty catch block
                        }
                    }
                }
            }
        }
        Random r = new Random();
        ArrayList<EvolutionInfo> arrayList = this.getFinalEvolution(evol, digimon);
        return arrayList.get(r.nextInt(arrayList.size()));
    }

    public String getPartnerAttribute(Enum.Attribute evolsAttribute, PhysicalState d) {
        return d.getAffinity().getPartnerAttributeAsString(evolsAttribute, d.getAttribute());
    }

    public void jogress(String jogressMatch, PhysicalState digimon, EvolutionInfo newEvol, ArrayList<EvolutionInfo> evolDigimon, int partner) {
        this.digivolve(this.pairJogressMatch(digimon, jogressMatch), digimon, evolDigimon, false, partner);
    }

    public void digivolve(EvolutionInfo finalEvolution, PhysicalState digimon, ArrayList<EvolutionInfo> evolDigimon, boolean revert, int partner) {
        int id;
        EvolutionInfo currentEvol = this.getDigimon(digimon.getIndex());
        if (finalEvolution.getSpecialEvol() != Enum.SpecialEvolution.Mode && !revert) {
            digimon.getEvolHistory().add(new int[]{finalEvolution.getIndex(), partner});
            Taste foodRanks = digimon.getFoodRanks();
            Taste timeRanks = digimon.getTimeRanks();
            Taste attributeRanks = digimon.getAttributeRanks();
            foodRanks.getRank(Enum.Food.Meat).incRank(finalEvolution.getMeatRank());
            foodRanks.getRank(Enum.Food.Fish).incRank(finalEvolution.getFishRank());
            foodRanks.getRank(Enum.Food.Veg).incRank(finalEvolution.getVegRank());
            foodRanks.getRank(Enum.Food.Fruit).incRank(finalEvolution.getFruitRank());
            foodRanks.getRank(Enum.Food.Grain).incRank(finalEvolution.getGrainRank());
            foodRanks.getRank(Enum.Food.Dairy).incRank(finalEvolution.getDairyRank());
            foodRanks.getRank(Enum.Food.Med).incRank(finalEvolution.getMedRank());
            foodRanks.getRank(Enum.Food.Junk).incRank(finalEvolution.getJunkRank());
            timeRanks.getRank(Enum.Time.Morning).incRank(finalEvolution.getMorningRank());
            timeRanks.getRank(Enum.Time.Noon).incRank(finalEvolution.getDayRank());
            timeRanks.getRank(Enum.Time.Night).incRank(finalEvolution.getNightRank());
            attributeRanks.getRank(Enum.Attribute.Vaccine).incRank(finalEvolution.getVaccineRank());
            attributeRanks.getRank(Enum.Attribute.Data).incRank(finalEvolution.getDataRank());
            attributeRanks.getRank(Enum.Attribute.Virus).incRank(finalEvolution.getVirusRank());
            if (finalEvolution.resetEvolVars()) {
                digimon.resetEvolVar();
            }
            digimon.setEnergy((byte)(digimon.getEnergy() + Config._evolutionEnergyChange));
        } else {
            digimon.replaceEvolHistory(digimon.getIndex(), finalEvolution.getIndex());
        }
        evolDigimon.get(finalEvolution.getIndex()).setUnlocked(true);
        this.checkNaturalUnlocked();
        Enum.Stage newStage = finalEvolution.getNewStage();
        int newWeight = this.proportionalWeightChange(digimon, finalEvolution, revert);
        digimon.loadSpeciesData(finalEvolution);
        digimon.setWeight(newWeight);
        if (finalEvolution.getSpecialEvol() != Enum.SpecialEvolution.Mode && !revert) {
            int[] periodLife;
            switch (newStage) {
                case Egg: {
                    periodLife = this.egg(digimon, finalEvolution);
                    break;
                }
                case Fresh: {
                    periodLife = this.fresh(digimon);
                    break;
                }
                case InTraining: {
                    periodLife = this.inTraining(digimon);
                    break;
                }
                case Rookie: {
                    periodLife = this.rookie(digimon);
                    break;
                }
                case Champion: {
                    periodLife = this.champion(digimon);
                    break;
                }
                case Ultimate: {
                    periodLife = this.ultimate(digimon);
                    break;
                }
                case Mega: {
                    periodLife = this.mega(digimon);
                    break;
                }
                default: {
                    periodLife = new int[]{0, 0};
                }
            }
            switch (finalEvolution.getXAntibody()) {
                case Natural: 
                case Induced: {
                    digimon.setXAntibodyState(Enum.XAntibodyState.Permanent);
                }
            }
            periodLife[0] = periodLife[0] + finalEvolution.getGrowthPeriodMod();
            periodLife[1] = periodLife[1] + finalEvolution.getLifespanMod();
            digimon.setTotalLifespan(digimon.getTotalLifespan() + (long)Utility.calcVariance(Config._lifespanVariance, periodLife[1]), false);
            digimon.setGrowthPeriod(digimon.getGrowthPeriod() + (long)Utility.calcVariance(Config._growthPeriodVariance, periodLife[0]));
            this.bonusLifespan(digimon);
        }
        if ((id = finalEvolution.getGiveItem()) >= 0) {
            digimon.setUnlockConsumable(id);
        }
        digimon.attributeEvolChange(revert ? currentEvol : finalEvolution, revert);
        if (Config._evolveRefreshEnergy && finalEvolution.getSpecialEvol() != Enum.SpecialEvolution.Mode && !revert && partner == -1 && finalEvolution.getEvolItemID() == -1 && finalEvolution.getEvolFoodID() == -1) {
            digimon.setEnergy(digimon.getMaxEnergy());
        }
        digimon.autoSave();
    }

    private int proportionalWeightChange(PhysicalState digimon, EvolutionInfo evol, boolean revert) {
        int weight = 0;
        if (evol.getSpecialEvol() != Enum.SpecialEvolution.Mode && !revert) {
            weight = evol.getNewWeight();
        } else {
            double p = (double)digimon.getWeight() / (double)digimon.getBaseWeight();
            weight = (int)Math.round(p * (double)evol.getNewWeight());
        }
        return weight;
    }

    private int[] egg(PhysicalState digimon, EvolutionInfo e) {
        digimon.setRawExercise(Config._fullStrength);
        digimon.setRawHunger(Config._fullHunger);
        digimon.setMood(Config._eggMood);
        digimon.resetToEgg();
        digimon.setGrowthStage(Enum.Stage.Egg);
        return new int[]{Config._eggGrowthPeriodInc, Config._eggGrowthLifeInc};
    }

    private int[] fresh(PhysicalState _myDigimon) {
        _myDigimon.setTemp((_myDigimon.getIdealTemp()[0] + _myDigimon.getIdealTemp()[1]) / 2);
        _myDigimon.setGrowthStage(Enum.Stage.Fresh);
        _myDigimon.setMood(Config._freshMood);
        _myDigimon.setObedience(Utility.randomBetween(Config._freshObedienceMin, Config._freshObedienceMax));
        _myDigimon.setRawExercise(0);
        _myDigimon.setRawHunger(0);
        _myDigimon.setEnergy(_myDigimon.getMaxEnergy());
        _myDigimon.setProtein(Config._startProtein);
        _myDigimon.setMineral(Config._startMineral);
        _myDigimon.setVitamin(Config._startVitamin);
        return new int[]{Config._freshPeriod, Config._freshLifeInc};
    }

    private int[] inTraining(PhysicalState _myDigimon) {
        if (_myDigimon.getObedience() > Config._inTrainingObedienceMin) {
            _myDigimon.setObedience(Utility.randomBetween(Config._inTrainingObedienceMin, Config._inTrainingObedienceMax));
        }
        _myDigimon.setAsleep(false);
        _myDigimon.setLights(true);
        _myDigimon.setSleepLapse(Config._inTrainingSleepLapse);
        _myDigimon.setGrowthStage(Enum.Stage.InTraining);
        return new int[]{Config._inTrainingPeriod, Config._inTrainingLifeInc};
    }

    private int[] rookie(PhysicalState _myDigimon) {
        int o = 0;
        if (o < 0) {
            o = 0;
        }
        switch (_myDigimon.getDailyMood()) {
            case Happy: {
                _myDigimon.setObedience(Utility.randomBetween(Config._rookieGoodObedienceMin + o, Config._rookieGoodObedience + o));
                break;
            }
            case Neutral: {
                _myDigimon.setObedience(Utility.randomBetween(Config._rookieDefaultObedienceMin + o, Config._rookieDefaultObedience + o));
                break;
            }
            default: {
                _myDigimon.setObedience(Config._rookieBadObedience + o);
            }
        }
        _myDigimon.setGrowthStage(Enum.Stage.Rookie);
        return new int[]{Config._rookiePeriod, Config._rookieLifeInc};
    }

    private int[] champion(PhysicalState _myDigimon) {
        double winRate = (double)_myDigimon.getWins() / (double)_myDigimon.getBattles() * 100.0;
        _myDigimon.setBonus(_myDigimon.getBonus() + (int)(Config._winRateRookieBonusIncCoefficient * winRate - 5.0));
        _myDigimon.randOnChampion();
        _myDigimon.setGrowthStage(Enum.Stage.Champion);
        return new int[]{Config._championPeriod, Config._championLifeInc};
    }

    private int[] ultimate(PhysicalState _myDigimon) {
        _myDigimon.setGrowthStage(Enum.Stage.Ultimate);
        return new int[]{Config._ultimatePeriod, Config._ultimateLifeInc};
    }

    private int[] mega(PhysicalState _myDigimon) {
        _myDigimon.setGrowthStage(Enum.Stage.Mega);
        return new int[]{Config._megaPeriod, Config._megaLifeInc};
    }

    private void bonusLifespan(PhysicalState digimon) {
        digimon.setTotalLifespan(digimon.getTotalLifespan() + (long)(Config._bonusEvolutionLife * digimon.getBonus()));
    }

    private int daysToSeconds(double days) {
        return (int)(days * (double)Config._hoursDay * (double)Config._minutesHour * (double)Config._secondsMinute);
    }

    public boolean evolve(PhysicalState digimon, int item, int food, boolean dying, boolean modeChange, int probChange) {
        return this.checkEvol(digimon, this.getDigimon(digimon.getIndex()), this._evolDigimon, item, food, dying, modeChange, probChange);
    }

    public boolean canFoodEvolve(int index) {
        ArrayList<EvolutionInfo> evolutions = this.getDigimon(index).getEvolutions();
        for (EvolutionInfo e : evolutions) {
            if (e.getEvolFoodID() <= -1) continue;
            return true;
        }
        return false;
    }

    public ArrayList<EvolutionInfo> getCurrentNaturalEvol(PhysicalState digimon) {
        if (digimon.getLapsedLife() < digimon.getGrowthPeriod()) {
            return this.getValidEvolutionFromList(digimon, this.getDigimon(digimon.getIndex()), this._evolDigimon, -1, -1, false, false, 0);
        }
        return null;
    }

    public boolean revert(PhysicalState digimon, int id) {
        boolean success = false;
        EvolutionInfo current = this.getDigimon(digimon.getIndex());
        if (digimon.getVaccinePower() - current.getVaccineChange() >= 0 && digimon.getDataPower() - current.getDataChange() >= 0 && digimon.getVirusPower() - current.getVirusChange() >= 0) {
            EvolutionInfo e = this.getDigimon(id);
            success = true;
            this.digivolve(e, digimon, this._evolDigimon, true, -1);
        }
        return success;
    }

    public boolean canEvolve(PhysicalState digimon) {
        boolean canEvolve = false;
        EvolutionInfo evolDigimon = this.getDigimon(digimon.getIndex());
        if (evolDigimon.getEvolutions().size() > 0) {
            canEvolve = true;
        }
        return canEvolve;
    }

    public boolean canModeChange(int id) {
        boolean b = false;
        EvolutionInfo digimon = this.getDigimon(id);
        if (digimon.getEvolutions() != null) {
            for (EvolutionInfo e : digimon.getEvolutions()) {
                if (e == null || e.getSpecialEvol() != Enum.SpecialEvolution.Mode) continue;
                b = true;
                break;
            }
        }
        return digimon.getSpecialEvol() == Enum.SpecialEvolution.Mode || b;
    }

    public int getNormalEvolutionCount(int id) {
        EvolutionInfo digimon = this.getDigimon(id);
        int i = 0;
        if (digimon.getEvolutions() != null) {
            for (EvolutionInfo e : digimon.getEvolutions()) {
                if (e == null || e.getSpecialEvol() != Enum.SpecialEvolution.None) continue;
                ++i;
            }
        }
        return i;
    }

    public String jogress(PhysicalState digimon) {
        String evolved = "";
        for (int i = 0; i < this._evolDigimon.size(); ++i) {
            if (digimon.getIndex() != this._evolDigimon.get(i).getIndex()) continue;
            evolved = this.checkJogress(digimon, this._evolDigimon.get(i));
            break;
        }
        return evolved;
    }

    public EvolutionInfo getDigimon(int index) {
        EvolutionInfo digimon = null;
        for (int i = 0; i < this._evolDigimon.size(); ++i) {
            if (this._evolDigimon.get(i) == null || this._evolDigimon.get(i).getIsNatural() || this._evolDigimon.get(i).getIndex() != index) continue;
            digimon = this._evolDigimon.get(i);
            break;
        }
        return digimon;
    }

    public ArrayList<EvolutionInfo> getDigimonList(String name) {
        ArrayList<EvolutionInfo> digimon = new ArrayList<EvolutionInfo>();
        for (int i = 0; i < this._evolDigimon.size(); ++i) {
            if (this._evolDigimon.get(i) == null || this._evolDigimon.get(i).getIsNatural() || !name.toUpperCase().equals(this._evolDigimon.get(i).getName().toUpperCase())) continue;
            digimon.add(this._evolDigimon.get(i));
        }
        return digimon;
    }

    public EvolutionInfo getDigimon(String name) {
        EvolutionInfo digimon = new EvolutionInfo();
        for (int i = 0; !(i >= this._evolDigimon.size() || this._evolDigimon.get(i) != null && !this._evolDigimon.get(i).getIsNatural() && name.toUpperCase().equals(this._evolDigimon.get(i).getName().toUpperCase()) && (digimon = this._evolDigimon.get(i)).getUnlocked()); ++i) {
        }
        return digimon;
    }

    public ArrayList<EvolutionInfo> getStages(Enum.Stage s) {
        ArrayList<EvolutionInfo> e = new ArrayList<EvolutionInfo>();
        for (EvolutionInfo digimon : this._evolDigimon) {
            if (digimon.getNewStage() != s) continue;
            e.add(digimon);
        }
        return e;
    }

    public ArrayList<EvolutionInfo> getStartingDigimon() {
        ArrayList<EvolutionInfo> e = new ArrayList<EvolutionInfo>();
        for (EvolutionInfo digimon : this._evolDigimon) {
            if (!digimon.isStarter()) continue;
            e.add(digimon);
        }
        Collections.sort(e, Comparator.comparing(EvolutionInfo::isListPriority, Comparator.reverseOrder()));
        return e;
    }

    public ArrayList<EvolutionInfo> getRestartDigimon() {
        ArrayList<EvolutionInfo> e = new ArrayList<EvolutionInfo>();
        for (EvolutionInfo digimon : this._evolDigimon) {
            if (!digimon.isRestarter()) continue;
            e.add(digimon);
        }
        Collections.sort(e, Comparator.comparing(EvolutionInfo::isListPriority, Comparator.reverseOrder()));
        return e;
    }

    public int getRandomAssistDigimon() {
        ArrayList<EvolutionInfo> e = new ArrayList<EvolutionInfo>();
        for (EvolutionInfo digimon : this._evolDigimon) {
            if (!digimon.canAssist()) continue;
            e.add(digimon);
        }
        if (e.size() > 0) {
            Random r = new Random();
            return ((EvolutionInfo)e.get(r.nextInt(e.size()))).getIndex();
        }
        return -1;
    }

    private void readDigimon() {
        try (InputStream in = Utility.getInputStream(this.MOD_FOLDER, this.MODEL_FOLDER, "digimon.csv");
             BufferedReader reader = new BufferedReader(new InputStreamReader(in, "utf-8"));){
            String line = reader.readLine();
            while ((line = reader.readLine()) != null) {
                EvolutionInfo evol = new EvolutionInfo();
                this._evolDigimon.add(evol.readInfoString(line));
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void writeStageEvolutions(Enum.Stage stage) {
        try (PrintWriter save = new PrintWriter("stageEvol.csv");){
            for (EvolutionInfo evol : this._evolDigimon) {
                if (evol.getNewStage() != stage) continue;
                String s = evol.getIndex() + ",";
                block8: for (EvolutionInfo e : evol.getEvolutions()) {
                    if (e.getIsNatural()) {
                        for (int i = 1455; i < this._evolDigimon.size(); ++i) {
                            if (!this._evolDigimon.get(i).getName().equals(e.getName())) continue;
                            s = s + i + ",";
                            continue block8;
                        }
                        continue;
                    }
                    s = s + e.getIndex() + ",";
                }
                save.println(s);
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void writeDigimon() {
        try (PrintWriter save = new PrintWriter("newDigimon.csv");){
            save.println("IsNatural,Name,EggType,NewStage,NewSpriteNum,NewSpriteSet,NewAttribute,NewField,EvolutionsLength,Difficulty,IsJogress,VaccinePowerFirstKey,VaccinePowerFirstValue,VaccinePowerSecondKey,VaccinePowerSecondValue,DataPowerFirstKey,DataPowerFirstValue,DataPowerSecondKey,DataPowerSecondValue,VirusPowerFirstKey,VirusPowerFirstValue,VirusPowerSecondKey,VirusPowerSecondValue,WeightKey,WeightValue,NewWeight,StomachCapacity,Time,DisturbKey,DisturbValue,OvereatKey,OvereatValue,SickKey,SickValue,InjuredKey,InjuredValue,MoodKey,MoodValue,ObedienceKey,ObedienceValue,BattlesKey,BattlesValue,WinsKey,WinsValue,MistakesKey,MistakesValue,Probability");
            for (EvolutionInfo digimon : this._evolDigimon) {
                save.println(digimon.infoToString());
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void readEvolutions() {
        try (InputStream in = Utility.getInputStream(this.MOD_FOLDER, this.MODEL_FOLDER, "evolutions.csv");
             BufferedReader reader = new BufferedReader(new InputStreamReader(in));){
            String line;
            reader.readLine();
            while ((line = reader.readLine()) != null) {
                this.addEvol(line);
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    private String writeSpiritsToEvolCSV(String s) {
        String[] data = s.split(",");
        ArrayList<String> evol = new ArrayList<String>(Arrays.asList(data));
        int digimon = Integer.parseInt(data[0]);
        EvolutionInfo e = this.getDigimon(digimon);
        if (e.getNewStage() == Enum.Stage.Rookie) {
            switch (e.getNewElement()) {
                case Fire: {
                    evol.add("1105");
                    break;
                }
                case Light: {
                    evol.add("1106");
                    break;
                }
                case Ice: {
                    evol.add("1107");
                    break;
                }
                case Wind: {
                    evol.add("1108");
                    break;
                }
                case Thunder: {
                    evol.add("1109");
                    break;
                }
                case Earth: {
                    evol.add("1110");
                    break;
                }
                case Water: {
                    evol.add("1111");
                    break;
                }
                case Wood: {
                    evol.add("1112");
                    break;
                }
                case Metal: {
                    evol.add("1113");
                    break;
                }
                case Dark: {
                    evol.add("1114");
                    break;
                }
            }
        }
        String finalEvol = "";
        for (String string : evol) {
            finalEvol = finalEvol + string + ",";
        }
        return finalEvol;
    }

    private void writeEvolutions() {
        try (PrintWriter save = new PrintWriter("evolutions.csv");){
            for (EvolutionInfo evol : this._evolDigimon) {
                save.println(evol.evolutionsToString());
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void initEvolDigimon() {
        this._evolDigimon = new ArrayList();
        this.readDigimon();
        System.out.println(this._evolDigimon.size());
        this.setEvolTree();
    }

    private void setEvolTree() {
        this.readEvolutions();
        this.setNaturals();
    }

    private void setNaturals() {
        for (int i = 0; i < this._evolDigimon.size(); ++i) {
            if (this._evolDigimon.get(i).getNaturalParent() == -1) continue;
            this.naturalEvol(this._evolDigimon.get(i));
        }
    }

    public void checkNaturalUnlocked() {
        block0: for (EvolutionInfo e : this._evolDigimon) {
            if (!e.getIsNatural()) continue;
            for (EvolutionInfo d : this._evolDigimon) {
                if (!d.getUnlocked() || !e.getName().equals(d.getName())) continue;
                e.setUnlocked(d.getUnlocked());
                continue block0;
            }
        }
    }

    private void addEvol(String datum) {
        String[] data = datum.split(",");
        int digimon = Integer.parseInt(data[0]);
        ArrayList<Integer> evolutions = new ArrayList<Integer>();
        for (int i = 1; i < data.length; ++i) {
            if (data[i].length() == 0) continue;
            evolutions.add(Integer.parseInt(data[i]));
        }
        this.getDigimon(digimon).addEvolutions(evolutions.toArray(new Integer[evolutions.size()]), this._evolDigimon, true);
    }

    private void naturalEvol(EvolutionInfo digimon) {
        EvolutionInfo naturalEvol = this.getDigimon(digimon.getNaturalParent());
        EvolutionInfo newEvol = new EvolutionInfo(naturalEvol.getIndex(), naturalEvol.getNaturalParent(), naturalEvol.getName(), naturalEvol.isStarter(), naturalEvol.getNewStage(), naturalEvol.getNewSpriteNum(), naturalEvol.getNewSpriteSet(), naturalEvol.getNewAttribute(), naturalEvol.getNewField(), naturalEvol.getNewElement(), naturalEvol.getVaccineName(), naturalEvol.getVaccineEffect(), naturalEvol.getVaccineConditions(), naturalEvol.getDataName(), naturalEvol.getDataEffect(), naturalEvol.getDataConditions(), naturalEvol.getVirusName(), naturalEvol.getVirusEffect(), naturalEvol.getVirusConditions(), naturalEvol.getPreEvolutions(), naturalEvol.getEvolutions(), naturalEvol.getPriority(), naturalEvol.getSpecialEvol(), naturalEvol.getRawVaccine(), naturalEvol.getRawData(), naturalEvol.getRawVirus(), naturalEvol.getWeight(), naturalEvol.getNewWeight(), naturalEvol.getStomachCapacity(), naturalEvol.getTime(), naturalEvol.getRawDisturb(), naturalEvol.getRawOvereat(), naturalEvol.getRawSick(), naturalEvol.getRawInjured(), naturalEvol.getMood(), naturalEvol.getRawObedience(), naturalEvol.getRawBattles(), naturalEvol.getRawWins(), naturalEvol.getRawMistakes(), naturalEvol.getIdealTemp(), naturalEvol.getTempReq(), naturalEvol.getMajorFood(), naturalEvol.getRawIncarnations(), naturalEvol.getLevelFought(), naturalEvol.getRawLevelFoughtCondition(), naturalEvol.getXAntibody(), naturalEvol.getRawVirusBuster(), naturalEvol.getRawMetalEmpire(), naturalEvol.getRawDragonsRoar(), naturalEvol.getRawJungleTrooper(), naturalEvol.getRawDeepSea(), naturalEvol.getRawNightmareSoldier(), naturalEvol.getRawWindGuardian(), naturalEvol.getRawNatureSpirit(), naturalEvol.getRawDarkArea(), naturalEvol.getRawNone(), naturalEvol.getVaccineChange(), naturalEvol.getDataChange(), naturalEvol.getVirusChange(), naturalEvol.getLifespanMod(), naturalEvol.getGrowthPeriodMod(), naturalEvol.getEvolItemID(), naturalEvol.getProb(), naturalEvol.getHabitat(), naturalEvol.getTournamentAble(), naturalEvol.getHiddenEvolution(), naturalEvol.getHiddenPreEvolution(), naturalEvol.getShowEvolutions(), naturalEvol.getShowPreEvolutions(), naturalEvol.getMeatRank(), naturalEvol.getFishRank(), naturalEvol.getVegRank(), naturalEvol.getFruitRank(), naturalEvol.getMorningRank(), naturalEvol.getDayRank(), naturalEvol.getNightRank(), naturalEvol.getVaccineRank(), naturalEvol.getDataRank(), naturalEvol.getVirusRank(), naturalEvol.getFoodPreference(), naturalEvol.getTimePreference(), naturalEvol.getAttributePreference(), naturalEvol.getMaxEnergy(), naturalEvol.getMaxStrength(), naturalEvol.getEnergyGain(), naturalEvol.getNapEnergyGain(), null, naturalEvol.getHungerDecayCoefficient(), naturalEvol.getStrengthDecayCoefficient(), naturalEvol.getSleepLapseInc(), naturalEvol.getAwakeLapseInc(), naturalEvol.getBMLapseInc(), naturalEvol.getBMMax(), naturalEvol.getGiveItem(), naturalEvol.getEvolFoodID(), naturalEvol.isRestarter(), naturalEvol.getSpriteRotations(), naturalEvol.isListPriority(), naturalEvol.canAssist(), naturalEvol.getMedRank(), naturalEvol.getJunkRank(), naturalEvol.getGrainRank(), naturalEvol.getDairyRank(), naturalEvol.getFoodAversion(), naturalEvol.getTimeAversion(), naturalEvol.getAttributeAversion(), naturalEvol.getFoodIntolerance(), naturalEvol.resetEvolVars(), naturalEvol.getSleepMinutesToEnergyGain(), naturalEvol.getPoopSickBoundMultiplier(), naturalEvol.getFilthLapseMoodChange(), naturalEvol.getUnlocked());
        newEvol.setNatural();
        digimon.addEvolution(newEvol, false);
        this._evolDigimon.add(newEvol);
        String[] preEvolution = new String[]{digimon.getName()};
        this.getDigimon(newEvol.getIndex()).addPreEvolutions(preEvolution, this._evolDigimon);
    }
}

