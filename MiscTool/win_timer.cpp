#include <windows.h>
#include <wchar.h>

/* Open x64 native tools command prompt 
   cl p1.cpp
   p1
 */
/*
typedef struct _SYSTEMTIME {
    WORD wYear;
    WORD wMonth;
    WORD wDayOfWeek;
    WORD wDay;
    WORD wHour;
    WORD wMinute;
    WORD wSecond;
    WORD wMilliseconds;
} SYSTEMTIME, *PSYSTEMTIME, *LPSYSTEMTIME;
*/

UINT64 getTimeInEpochMilliSeconds(SYSTEMTIME *pSysTime)
{
	SYSTEMTIME     sysTime = { 0 }, epochFormat = { 0 };
	FILETIME       fileTime = { 0 }, epochFileTime = { 0 };
	ULARGE_INTEGER time = { 0 }, epochTime = { 0 };
	UINT64         milliSec = 0;

	if (pSysTime == NULL)
	{
		GetSystemTime(&sysTime);
		pSysTime = &sysTime;
	}

	SystemTimeToFileTime(pSysTime, &fileTime);

	time.u.HighPart = fileTime.dwHighDateTime;
	time.u.LowPart = fileTime.dwLowDateTime;

	epochFormat.wYear = 1970;
	epochFormat.wMonth = 1;
	epochFormat.wDay = 1;
	epochFormat.wDayOfWeek = 4;
	SystemTimeToFileTime(&epochFormat, &epochFileTime);
	epochTime.u.HighPart = epochFileTime.dwHighDateTime;
	epochTime.u.LowPart = epochFileTime.dwLowDateTime;

	milliSec = ((time.QuadPart - epochTime.QuadPart) / 10000);

      return milliSec;
}


int wmain(void) {

    SYSTEMTIME lt = {0};
    SYSTEMTIME sysTime;
    UINT64 millisec; 

    GetLocalTime(&lt);
  
    wprintf(L"The local time is: %02d:%02d:%02d\n", lt.wHour, lt.wMinute, lt.wSecond);

    for (int i=0; i<5; i++) {
        GetSystemTime(&sysTime);
        wprintf(L"GetSystemTime : Year %d Month %d Day %d Hour %d Min %d Sec %d MillSec %d\n",
                sysTime.wYear, sysTime.wMonth, sysTime.wDay, sysTime.wHour, sysTime.wMinute,
                sysTime.wSecond, sysTime.wMilliseconds);

        millisec = getTimeInEpochMilliSeconds(&sysTime);
        wprintf(L"getTimeInEpochMilliSeconds %I64u\n", millisec);
        Sleep(1*1000);
    }
    return 0;
}
