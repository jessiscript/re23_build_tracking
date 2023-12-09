package gameoflife;

import java.util.concurrent.LinkedBlockingDeque;

public class Channel<T> {
    private final LinkedBlockingDeque<T> queue = new LinkedBlockingDeque<>();

    T take() {
        try {
            return queue.take();
        } catch (InterruptedException e) {
            return null;
        }
    }

    void put(T value) {
        try {
            queue.put(value);
        } catch (InterruptedException e) {
            // abort
        }
    }
}
