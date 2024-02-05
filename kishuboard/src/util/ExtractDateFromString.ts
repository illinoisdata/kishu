export function extractDateFromString(dateString: string) {
    return dateString.substring(0, 10)
}

export function extractTimeFromString(dataString: string){
    return dataString.substring(10,19)
}

export function formatDate(dateString: string): string {
    const options: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'short', day: 'numeric' };
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', options);
}