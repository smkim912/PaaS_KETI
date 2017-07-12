#include <openssl/evp.h>
#include <openssl/rand.h>

#define MAX_BUFF_SIZE 2048   
typedef unsigned char U8;
static const U8 cipher_key[]= "KETI12345678901234561234567890123456";

EVP_CIPHER_CTX ctx_encrypt_aes;
EVP_CIPHER_CTX ctx_encrypt_des;
EVP_CIPHER_CTX ctx_decript_aes;
EVP_CIPHER_CTX ctx_decript_des;

int aes_des_encrypt( U8 *p_in, U8 *p_out, int size)
{
	int outlen;
	U8  buff[MAX_BUFF_SIZE];

	outlen  = 0;
	if ( !EVP_EncryptUpdate( &ctx_encrypt_aes, buff, &outlen, p_in, size)){
		return -1;
	}
	outlen  = 0;
	if ( !EVP_EncryptUpdate( &ctx_encrypt_des, p_out, &outlen, buff, size)){
		return -1;
	}

	return outlen;
}

int aes_des_decrypt( U8 *p_in, U8 *p_out, int size)
{
	int outlen;
	U8  buff[MAX_BUFF_SIZE];

	outlen  = 0;
	if ( !EVP_DecryptUpdate( &ctx_decript_des, buff, &outlen, p_in, size)){
		return -1;
	}
	outlen  = 0;
	if ( !EVP_DecryptUpdate( &ctx_decript_aes, p_out, &outlen, buff, size)){
		return -1;
	}

	return outlen;
}

int aes_des_init()
{
	EVP_CIPHER_CTX_init(&ctx_encrypt_aes);
	EVP_EncryptInit(&ctx_encrypt_aes, EVP_aes_256_cfb8(), cipher_key, NULL);
	EVP_CIPHER_CTX_init(&ctx_encrypt_des);
	EVP_EncryptInit(&ctx_encrypt_des, EVP_des_cfb(), cipher_key, NULL);

	EVP_CIPHER_CTX_init( &ctx_decript_aes);
	EVP_DecryptInit(&ctx_decript_aes, EVP_aes_256_cfb8(), cipher_key, NULL);
	EVP_CIPHER_CTX_init( &ctx_decript_des);
	EVP_DecryptInit( &ctx_decript_des, EVP_des_cfb(), cipher_key, NULL);
	return 0;
}

int aes_des_release()
{
	EVP_CIPHER_CTX_cleanup( &ctx_decript_aes);
	EVP_CIPHER_CTX_cleanup( &ctx_decript_des);
	EVP_CIPHER_CTX_cleanup( &ctx_encrypt_aes);
	EVP_CIPHER_CTX_cleanup( &ctx_encrypt_des);
	return 0;
}
