/*
 * Decompiled with CFR 0.152.
 */
package Controller;

import Model.CrashEntry;

public class IncorrectRequirement
extends RuntimeException {
    public IncorrectRequirement(String errorMessage) {
        super(errorMessage);
        CrashEntry.generateEntry(this);
    }
}

