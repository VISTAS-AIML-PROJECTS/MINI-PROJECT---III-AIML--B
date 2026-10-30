package com.genvoice.caregiver.data.api

import com.genvoice.caregiver.utils.Constants
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * Retrofit API client singleton
 */
object ApiClient {

    /**
     * Lazy-initialized Retrofit instance
     */
    private val retrofit: Retrofit by lazy {
        Retrofit.Builder()
            .baseUrl(Constants.BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    /**
     * OkHttp client with interceptors
     */
    private val okHttpClient: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .connectTimeout(Constants.API_TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .readTimeout(Constants.API_TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .writeTimeout(Constants.API_TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .addInterceptor(loggingInterceptor)
            .addInterceptor(headerInterceptor)
            .retryOnConnectionFailure(true)
            .build()
    }

    /**
     * Logging interceptor for debugging
     */
    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    /**
     * Header interceptor to add common headers
     */
    private val headerInterceptor = Interceptor { chain ->
        val request = chain.request().newBuilder()
            .addHeader("Content-Type", "application/json")
            .addHeader("Accept", "application/json")
            .build()
        chain.proceed(request)
    }

    /**
     * Get GenVoice API service instance
     */
    val api: GenVoiceApi by lazy {
        retrofit.create(GenVoiceApi::class.java)
    }

    /**
     * Check if backend is reachable
     */
    suspend fun isBackendReachable(): Boolean {
        return try {
            val response = api.health()
            response.isSuccessful
        } catch (e: Exception) {
            false
        }
    }
}

/**
 * Extension function for safe API calls
 */
suspend fun <T> safeApiCall(
    apiCall: suspend () -> retrofit2.Response<ApiResponse<T>>
): Result<T> {
    return try {
        val response = apiCall()
        if (response.isSuccessful) {
            val body = response.body()
            if (body != null && body.success && body.data != null) {
                Result.Success(body.data)
            } else {
                Result.Error(body?.error ?: body?.message ?: "Unknown error")
            }
        } else {
            Result.Error("HTTP ${response.code()}: ${response.message()}")
        }
    } catch (e: java.net.UnknownHostException) {
        Result.Error("No internet connection", e)
    } catch (e: java.net.SocketTimeoutException) {
        Result.Error("Connection timeout. Please try again.", e)
    } catch (e: java.net.ConnectException) {
        Result.Error("Cannot connect to server. Please check if backend is running.", e)
    } catch (e: Exception) {
        Result.Error("Network error: ${e.localizedMessage}", e)
    }
}
