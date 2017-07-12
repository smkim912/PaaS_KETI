CC = gcc

OBJS = dualenc
SRC = dualenc.c
CFLAGS = 

TARGET = libdualenc.so

all:$(SRC)
	$(CC) -shared -Wl,-soname,$(OBJS) -fPIC -lcrypto -o $(TARGET) $(SRC)

clean:
	rm -rf $(TARGET)
