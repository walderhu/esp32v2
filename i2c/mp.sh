mp() {
    ESP_HOST="192.168.0.248"
    ESP_PASS="1234"
    ESP_CLI="/home/des/miniforge3/envs/esp/bin/python /home/des/WORK/webrepl_cli.py -p $ESP_PASS"

    if [[ $# -eq 0 ]]; then
        $ESP_CLI "$ESP_HOST"
        return
    fi

    cmd="$1"
    local_file="$2"
    remote_file="$3"

    case "$cmd" in
        put)
            if [[ -z "$local_file" ]]; then
                echo "Specify local file to put"
                return 1
            fi
            [[ -z "$remote_file" ]] && remote_file="/$(basename "$local_file")"
            $ESP_CLI "$local_file" "$ESP_HOST:$remote_file"
            ;;
        get)
            if [[ -z "$local_file" ]]; then
                echo "Specify remote file to get"
                return 1
            fi
            [[ -z "$remote_file" ]] && remote_file="$(basename "$local_file")"
            $ESP_CLI "$ESP_HOST:$local_file" "$remote_file"
            ;;
        repl)
            $ESP_CLI "$ESP_HOST"
            ;;
        *)
            [[ -z "$remote_file" ]] && remote_file="/$(basename "$cmd")"
            $ESP_CLI "$cmd" "$ESP_HOST:$remote_file"
            ;;
    esac
}
