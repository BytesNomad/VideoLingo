echo conda activate videolingo2
export https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 all_proxy=socks5://127.0.0.1:7890
export PYTORCH_ENABLE_MPS_FALLBACK=1
rm -rf output/
python batch/utils/batch_processor.py