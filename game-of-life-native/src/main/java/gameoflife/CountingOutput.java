package gameoflife;

import com.google.gson.Gson;

import java.lang.management.ManagementFactory;
import java.util.function.Consumer;

public class CountingOutput implements Consumer<boolean[][]> {
    static final int TIMED_STEPS = 1000;
    static final int WARMUP_STEPS = TIMED_STEPS;

    private int steps = 0;
    private long timingStartNanos;

    public CountingOutput(int numThreads, int numChannels) {
        System.out.printf("Startup time: %dms; Number of virtual threads: %d; Number of channels: %d%nWarming up", System.currentTimeMillis() - ManagementFactory.getRuntimeMXBean().getStartTime(), numThreads, numChannels);
    }

    @Override
    public void accept(boolean[][] cells) {
        steps++;
        if ((steps & 0xf) == 0) {
            System.out.print(".");
        }
        Gson gson = new Gson();
        if (steps == WARMUP_STEPS) {
            System.out.printf("%nStarting timer");
            timingStartNanos = System.nanoTime();
        } else if (steps == WARMUP_STEPS + TIMED_STEPS) {
            long millis = (System.nanoTime() - timingStartNanos) / 1_000_000;
            System.out.printf("%nCompleted %d steps in %dms = %f steps per second%n", TIMED_STEPS, millis, TIMED_STEPS / (millis / 1000.0));
            System.exit(0);
        }
    }
}
